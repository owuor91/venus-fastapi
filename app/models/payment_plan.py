import uuid
from sqlalchemy import Column, Float, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.enums import PlanEnum


class PaymentPlan(BaseModel):
    """
    PaymentPlan model for subscription plans.
    Inherits common fields from BaseModel:
    - date_created, date_updated, created_by, updated_by, active, meta
    """
    __tablename__ = "payment_plans"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    plan = Column(Enum(PlanEnum), nullable=False)
    amount = Column(Float, nullable=False)
    months = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<PaymentPlan(plan_id='{self.plan_id}', plan='{self.plan.value}', amount={self.amount})>"
