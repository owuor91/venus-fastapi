from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel


class PaymentBase(BaseModel):
    user_id: UUID
    payment_ref: Optional[str] = None
    payment_date: datetime
    valid_until: datetime
    amount: float
    plan_id: UUID
    mpesa_transaction_id: Optional[str] = None
    transaction_request: Optional[Dict[str, Any]] = None
    transaction_response: Optional[Dict[str, Any]] = None
    transaction_callback: Optional[Dict[str, Any]] = None
    transaction_status: Optional[str] = None
    date_completed: Optional[datetime] = None


class PaymentCreateRequest(BaseModel):
    """Request schema for creating a payment."""
    payment_ref: Optional[str] = None
    amount: float
    plan_id: UUID
    phone_number: Optional[str] = None  # Used for STK push initiation, not stored in database
    mpesa_transaction_id: Optional[str] = None
    transaction_request: Optional[Dict[str, Any]] = None
    transaction_response: Optional[Dict[str, Any]] = None


class PaymentCreate(PaymentBase):
    created_by: str
    updated_by: str


class PaymentUpdate(BaseModel):
    payment_ref: Optional[str] = None
    payment_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    amount: Optional[float] = None
    plan_id: Optional[UUID] = None
    mpesa_transaction_id: Optional[str] = None
    transaction_request: Optional[Dict[str, Any]] = None
    transaction_response: Optional[Dict[str, Any]] = None
    transaction_callback: Optional[Dict[str, Any]] = None
    transaction_status: Optional[str] = None
    date_completed: Optional[datetime] = None
    updated_by: str
    active: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


class PaymentInDB(PaymentBase):
    payment_id: UUID
    date_created: datetime
    date_updated: datetime
    created_by: str
    updated_by: str
    active: bool
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class Payment(PaymentInDB):
    pass
