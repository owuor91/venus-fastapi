import base64
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import requests
from requests.auth import HTTPBasicAuth

from app.core.config import settings
from app.models.payment import Payment
from app.models.payment_plan import PaymentPlan

logger = logging.getLogger(__name__)


def get_access_token() -> Optional[str]:
    """
    Get OAuth access token from Daraja API.
    
    Returns:
        str: Access token if successful, None otherwise
    """
    # Validate credentials are set
    if not settings.CONSUMER_KEY or not settings.CONSUMER_SECRET:
        logger.error("CONSUMER_KEY or CONSUMER_SECRET not set in environment variables")
        return None
    
    if not settings.DARAJA_CREDENTIALS_URL:
        logger.error("DARAJA_CREDENTIALS_URL not set in environment variables")
        return None
    
    try:
        response = requests.get(
            url=settings.DARAJA_CREDENTIALS_URL,
            auth=HTTPBasicAuth(settings.CONSUMER_KEY, settings.CONSUMER_SECRET),
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                logger.info("Successfully obtained Daraja access token")
                return access_token
            else:
                logger.error(f"Access token not found in response: {token_data}")
                return None
        else:
            logger.error(f"Failed to get Daraja access token: {response.status_code} - {response.text}")
            logger.error(f"Consumer Key (first 10 chars): {settings.CONSUMER_KEY[:10] if settings.CONSUMER_KEY else 'NOT SET'}...")
            return None
    except Exception as e:
        logger.error(f"Error getting Daraja access token: {str(e)}", exc_info=True)
        return None


def initiate_stk_push(payment: Payment, phone_number: str, plan: PaymentPlan, db) -> tuple[Dict[str, Any], int]:
    """
    Initiate STK push payment request to Daraja.
    
    Args:
        payment: Payment model instance
        phone_number: Customer phone number (format: 254712345678)
        plan: PaymentPlan model instance
        db: Database session
        
    Returns:
        tuple: (response_dict, status_code)
    """
    # Validate required settings
    if not settings.SHORT_CODE or not settings.DARAJA_PASSKEY:
        logger.error("SHORT_CODE or DARAJA_PASSKEY not set in environment variables")
        return {"error": "Daraja credentials not configured. Please set SHORT_CODE and DARAJA_PASSKEY"}, 500
    
    if not settings.DARAJA_STK_PUSH_URL:
        logger.error("DARAJA_STK_PUSH_URL not set in environment variables")
        return {"error": "DARAJA_STK_PUSH_URL not configured"}, 500
    
    access_token = get_access_token()
    if access_token is None:
        return {"error": "Failed to get Daraja access token. Please check CONSUMER_KEY and CONSUMER_SECRET"}, 500
    
    # Generate timestamp and password
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password_string = f"{settings.SHORT_CODE}{settings.DARAJA_PASSKEY}{timestamp}"
    password = base64.b64encode(
        bytes(password_string, "utf-8")
    ).decode("utf-8")
    
    logger.debug(f"STK Push - Short Code: {settings.SHORT_CODE}, Timestamp: {timestamp}")
    logger.debug(f"Password string (first 20 chars): {password_string[:20]}...")
    
    # Prepare request body
    req_body = {
        "BusinessShortCode": settings.SHORT_CODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(payment.amount),
        "PartyA": phone_number,
        "PartyB": settings.SHORT_CODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.DARAJA_CALLBACK_URL,
        "AccountReference": phone_number,
        "TransactionDesc": f"Venus {plan.plan.value}",
    }

    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            settings.DARAJA_STK_PUSH_URL,
            headers=headers,
            json=req_body,
            timeout=30
        )
        
        response_data = response.json() if response.content else {}
        
        if response.status_code != 200:
            error_code = response_data.get("errorCode", "Unknown")
            error_message = response_data.get("errorMessage", "Unknown error")
            logger.error(f"STK push failed: {response.status_code} - {error_code}: {error_message}")
            logger.error(f"Response data: {response_data}")
            
            # Provide helpful error messages
            if error_code == "500.001.1001":
                logger.error("Wrong credentials error - Please verify:")
                logger.error(f"  - SHORT_CODE: {settings.SHORT_CODE}")
                logger.error(f"  - DARAJA_PASSKEY: {'SET' if settings.DARAJA_PASSKEY else 'NOT SET'} (length: {len(settings.DARAJA_PASSKEY) if settings.DARAJA_PASSKEY else 0})")
                logger.error(f"  - CONSUMER_KEY: {'SET' if settings.CONSUMER_KEY else 'NOT SET'}")
                logger.error(f"  - CONSUMER_SECRET: {'SET' if settings.CONSUMER_SECRET else 'NOT SET'}")
            
            return response_data, response.status_code
        
        # Update payment with transaction details
        payment.transaction_request = req_body
        payment.transaction_response = response_data
        
        # Extract CheckoutRequestID from response
        checkout_request_id = response_data.get("CheckoutRequestID")
        if checkout_request_id:
            payment.mpesa_transaction_id = checkout_request_id
        
        payment.updated_by = payment.created_by
        db.commit()
        db.refresh(payment)
        
        logger.info(f"STK push initiated successfully for payment {payment.payment_id}")
        return response_data, response.status_code
        
    except Exception as e:
        logger.error(f"Error initiating STK push: {str(e)}", exc_info=True)
        return {"error": f"Something went wrong: {str(e)}"}, 400


def daraja_timestamp_to_datetime(timestamp_str: str) -> datetime:
    """
    Convert Daraja timestamp string to timezone-aware datetime.
    
    Args:
        timestamp_str: Timestamp string in format YYYYMMDDHHMMSS
        
    Returns:
        datetime: Timezone-aware datetime object
    """
    try:
        year = int(timestamp_str[:4])
        month = int(timestamp_str[4:6])
        day = int(timestamp_str[6:8])
        hour = int(timestamp_str[8:10])
        minute = int(timestamp_str[10:12])
        second = int(timestamp_str[12:14])
        
        dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
        return dt
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing Daraja timestamp {timestamp_str}: {str(e)}")
        return datetime.now(timezone.utc)


def get_payment_by_checkout_request_id(checkout_request_id: str, db) -> Optional[Payment]:
    """
    Get payment by M-Pesa checkout request ID.
    
    Args:
        checkout_request_id: M-Pesa CheckoutRequestID
        db: Database session
        
    Returns:
        Payment: Payment object if found, None otherwise
    """
    try:
        payment = db.query(Payment).filter(
            Payment.mpesa_transaction_id == checkout_request_id
        ).first()
        return payment
    except Exception as e:
        logger.error(f"Error getting payment by checkout request ID: {str(e)}", exc_info=True)
        return None
