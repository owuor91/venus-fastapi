import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class Match(BaseModel):
    """
    Match model for tracking matches between users.
    Inherits common fields from BaseModel:
    - date_created, date_updated, created_by, updated_by, active, meta
    """
    __tablename__ = "matches"

    match_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    my_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    thread_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    last_message = Column(String, nullable=True)
    last_message_date = Column(DateTime(timezone=True), nullable=True)
    sent_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True, index=True)
    
    # Unique constraint on (my_id, partner_id, thread_id)
    __table_args__ = (
        UniqueConstraint('my_id', 'partner_id', 'thread_id', name='uq_match_my_partner_thread'),
    )

    def __repr__(self):
        return f"<Match(match_id='{self.match_id}', my_id='{self.my_id}', partner_id='{self.partner_id}')>"
