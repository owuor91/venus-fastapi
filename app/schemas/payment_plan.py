from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.models.enums import PlanEnum


class PaymentPlanBase(BaseModel):
    plan: PlanEnum
    amount: float
    months: int


class PaymentPlanCreate(PaymentPlanBase):
    created_by: str
    updated_by: str


class PaymentPlanUpdate(BaseModel):
    plan: Optional[PlanEnum] = None
    amount: Optional[float] = None
    months: Optional[int] = None
    updated_by: str
    active: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


class PaymentPlanCreateRequest(BaseModel):
    plan: PlanEnum
    amount: float
    months: int
    active: bool = True
    meta: Optional[Dict[str, Any]] = None


class PaymentPlanInDB(PaymentPlanBase):
    plan_id: UUID
    date_created: datetime
    date_updated: datetime
    created_by: str
    updated_by: str
    active: bool
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class PaymentPlan(PaymentPlanInDB):
    pass
