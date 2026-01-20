from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.payment_plan import PaymentPlan
from app.schemas.payment_plan import PaymentPlan as PaymentPlanSchema
from app.schemas.payment_plan import PaymentPlanCreateRequest
from app.models.user import User
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("", response_model=PaymentPlanSchema, status_code=status.HTTP_201_CREATED)
def create_payment_plan(
    payment_plan: PaymentPlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new payment plan.
    """
    db_payment_plan = PaymentPlan(
        plan=payment_plan.plan,
        amount=payment_plan.amount,
        months=payment_plan.months,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
        active=payment_plan.active,
        meta=payment_plan.meta,
    )

    db.add(db_payment_plan)
    db.commit()
    db.refresh(db_payment_plan)
    return db_payment_plan


@router.get("", response_model=List[PaymentPlanSchema])
def get_payment_plans(
    db: Session = Depends(get_db)
):
    """
    Get all active payment plans.
    No authentication required.
    Only returns active payment plans.
    """
    plans = db.query(PaymentPlan).filter(
        PaymentPlan.active == True
    ).all()
    
    return plans
