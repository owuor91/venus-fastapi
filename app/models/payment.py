import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Payment(BaseModel):
    """
    Payment model for user payments.
    Inherits common fields from BaseModel:
    - date_created, date_updated, created_by, updated_by, active, meta
    """
    __tablename__ = "payments"

    payment_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True
    )
    payment_ref = Column(String, nullable=True)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Float, nullable=False)
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("payment_plans.plan_id"),
        nullable=False,
        index=True
    )
    mpesa_transaction_id = Column(String, nullable=True)
    transaction_request = Column(JSON, nullable=True)
    transaction_response = Column(JSON, nullable=True)
    transaction_callback = Column(JSON, nullable=True)
    transaction_status = Column(String, nullable=True)
    date_completed = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="payments")
    payment_plan = relationship("PaymentPlan", backref="payments")

    def __repr__(self):
        return (
            f"<Payment(payment_id='{self.payment_id}', "
            f"user_id='{self.user_id}', "
            f"amount={self.amount})>"
        )
