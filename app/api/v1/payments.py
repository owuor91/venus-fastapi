import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.payment import Payment
from app.models.payment_plan import PaymentPlan
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentUpdate,
    Payment as PaymentSchema
)
from app.api.deps import get_current_active_user
from app.core.daraja_helper import initiate_stk_push
from app.core.notifications import notifications

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=PaymentSchema,
    status_code=status.HTTP_201_CREATED
)
def create_payment(
    payment_data: PaymentCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new payment.
    Requires authentication.
    user_id is automatically set from the authenticated user.
    payment_date is automatically set to current timestamp.
    valid_until is automatically calculated based on payment plan's
    months.
    """
    # Get payment plan to calculate valid_until
    plan = db.query(PaymentPlan).filter(
        PaymentPlan.plan_id == payment_data.plan_id,
        PaymentPlan.active.is_(True)
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan_id or plan is not active"
        )

    # Set payment_date to current timestamp
    payment_date = datetime.now(timezone.utc)

    # Calculate valid_until: current time + plan.months
    valid_until = payment_date + relativedelta(months=plan.months)

    # Create payment record
    db_payment = Payment(
        user_id=current_user.user_id,
        payment_ref=payment_data.payment_ref,
        payment_date=payment_date,
        valid_until=valid_until,
        amount=payment_data.amount,
        plan_id=payment_data.plan_id,
        mpesa_transaction_id=payment_data.mpesa_transaction_id,
        transaction_request=payment_data.transaction_request,
        transaction_response=payment_data.transaction_response,
        created_by=str(current_user.user_id),
        updated_by=str(current_user.user_id),
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    return db_payment


@router.get("", response_model=List[PaymentSchema])
def get_user_payments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all active payments for the authenticated user.
    Requires authentication.
    Only returns active payments.
    """
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.user_id,
        Payment.active.is_(True)
    ).all()

    return payments


@router.get("/{payment_id}", response_model=PaymentSchema)
def get_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific payment by ID.
    Requires authentication.
    Only returns payments belonging to the authenticated user.
    """
    payment = db.query(Payment).filter(
        Payment.payment_id == payment_id,
        Payment.user_id == current_user.user_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return payment


@router.patch("/{payment_id}", response_model=PaymentSchema)
def update_payment(
    payment_id: UUID,
    payment_update: PaymentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update payment status (for callbacks/webhooks).
    Requires authentication.
    Only allows updating payments belonging to the authenticated user.
    """
    payment = db.query(Payment).filter(
        Payment.payment_id == payment_id,
        Payment.user_id == current_user.user_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Update fields
    if payment_update.payment_ref is not None:
        payment.payment_ref = payment_update.payment_ref
    if payment_update.payment_date is not None:
        payment.payment_date = payment_update.payment_date
    if payment_update.valid_until is not None:
        payment.valid_until = payment_update.valid_until
    if payment_update.amount is not None:
        payment.amount = payment_update.amount
    if payment_update.plan_id is not None:
        payment.plan_id = payment_update.plan_id
    if payment_update.mpesa_transaction_id is not None:
        payment.mpesa_transaction_id = payment_update.mpesa_transaction_id
    if payment_update.transaction_request is not None:
        payment.transaction_request = payment_update.transaction_request
    if payment_update.transaction_response is not None:
        payment.transaction_response = payment_update.transaction_response
    if payment_update.transaction_callback is not None:
        payment.transaction_callback = payment_update.transaction_callback
    if payment_update.transaction_status is not None:
        payment.transaction_status = payment_update.transaction_status
    if payment_update.date_completed is not None:
        payment.date_completed = payment_update.date_completed
    if payment_update.active is not None:
        payment.active = payment_update.active
    if payment_update.meta is not None:
        payment.meta = payment_update.meta

    payment.updated_by = payment_update.updated_by

    db.commit()
    db.refresh(payment)

    return payment


@router.post(
    "/initiate-stk",
    response_model=PaymentSchema,
    status_code=status.HTTP_201_CREATED
)
def initiate_stk_payment(
    payment_data: PaymentCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a payment and initiate STK push to customer's phone.
    Requires authentication.
    user_id is automatically set from the authenticated user.
    phone_number is required for STK push initiation.
    """
    if not payment_data.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="phone_number is required for STK push initiation"
        )

    # Validate payment plan exists
    plan = db.query(PaymentPlan).filter(
        PaymentPlan.plan_id == payment_data.plan_id,
        PaymentPlan.active.is_(True)
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan_id or plan is not active"
        )

    # Set payment_date to current timestamp
    payment_date = datetime.now(timezone.utc)

    # Calculate valid_until: current time + plan.months
    valid_until = payment_date + relativedelta(months=plan.months)

    # Create payment record
    db_payment = Payment(
        user_id=current_user.user_id,
        payment_ref=payment_data.payment_ref,
        payment_date=payment_date,
        valid_until=valid_until,
        amount=payment_data.amount,
        plan_id=payment_data.plan_id,
        mpesa_transaction_id=payment_data.mpesa_transaction_id,
        transaction_request=payment_data.transaction_request,
        transaction_response=payment_data.transaction_response,
        created_by=str(current_user.user_id),
        updated_by=str(current_user.user_id),
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    # Initiate STK push
    try:
        stk_response, stk_status_code = initiate_stk_push(
            db_payment,
            payment_data.phone_number,
            plan,
            db
        )

        if stk_status_code != 200:
            logger.warning(
                f"STK push failed for payment {db_payment.payment_id}: "
                f"{stk_response}"
            )
            # Payment record is still created, but STK push failed
    except Exception as e:
            logger.error(
                f"Error initiating STK push: {str(e)}",
                exc_info=True
            )
        # Payment record is still created even if STK push fails

    db.refresh(db_payment)
    return db_payment


@router.post("/callback")
def daraja_callback(
    callback_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Handle Daraja STK push callback.
    Public endpoint (no authentication required) - called by Daraja servers.
    """
    logger.debug("Received Daraja callback")
    logger.debug(f"Callback data: {callback_data}")

    try:
        # Parse callback structure
        body = callback_data.get("Body", {})
        stk_callback = body.get("stkCallback", {})
        result_code = stk_callback.get("ResultCode")

        if result_code != 0:
            logger.warning(
                f"Payment failed with result code: {result_code}"
            )
            logger.debug(
                f"Result description: {stk_callback.get('ResultDesc')}"
            )
            return JSONResponse(
                content={"status": "received", "result_code": result_code},
                status_code=status.HTTP_200_OK
            )

        # Extract callback metadata
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        callback_metadata = (
            stk_callback.get("CallbackMetadata", {}).get("Item", [])
        )

        if not checkout_request_id:
            logger.error("CheckoutRequestID not found in callback")
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "CheckoutRequestID not found"
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Find payment by checkout request ID
        payment = db.query(Payment).filter(
            Payment.mpesa_transaction_id == checkout_request_id
        ).first()

        if not payment:
            logger.error(
                f"Payment not found for CheckoutRequestID: "
                f"{checkout_request_id}"
            )
            return JSONResponse(
                content={"status": "error", "message": "Payment not found"},
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Extract payment details from callback metadata
        amount = 0
        mpesa_code = ""
        transaction_date = None

        for item in callback_metadata:
            name = item.get("Name")
            value = item.get("Value")

            if name == "Amount":
                amount = float(value) if value else 0
            elif name == "MpesaReceiptNumber":
                mpesa_code = str(value) if value else ""
            elif name == "TransactionDate":
                if value:
                    from app.core.daraja_helper import (
                        daraja_timestamp_to_datetime
                    )
                    transaction_date = daraja_timestamp_to_datetime(str(value))

        # Update payment with callback data
        payment.transaction_callback = callback_data
        payment.payment_ref = mpesa_code
        payment.date_completed = transaction_date

        # Get payment plan to compare amounts
        payment_plan = db.query(PaymentPlan).filter(
            PaymentPlan.plan_id == payment.plan_id
        ).first()

        if payment_plan:
            if amount >= payment_plan.amount:
                payment.transaction_status = "SUCCESSFUL"
            else:
                payment.transaction_status = "PARTIALLY_PAID"
                payment.amount = amount

        payment.updated_by = payment.created_by
        db.commit()
        db.refresh(payment)

        # Send payment notification to user
        user = db.query(User).filter(User.user_id == payment.user_id).first()
        if user and user.fcm_token:
            try:
                notifications.send_payment_notification(
                    payment,
                    user.fcm_token
                )
            except Exception as e:
                logger.error(
                    f"Failed to send payment notification: {str(e)}",
                    exc_info=True
                )

        logger.info(
            f"Payment {payment.payment_id} updated successfully "
            f"from callback"
        )
        return JSONResponse(
            content={
                "status": "success",
                "payment_id": str(payment.payment_id)
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(
            f"Error processing Daraja callback: {str(e)}",
            exc_info=True
        )
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
