import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Photo(BaseModel):
    """
    Photo model for user photo uploads.
    Inherits common fields from BaseModel:
    - date_created, date_updated, created_by, updated_by, active, meta
    """
    __tablename__ = "photos"

    photo_id = Column(
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
    photo_url = Column(String, nullable=False)
    verified = Column(Boolean, nullable=False, default=False)

    # Relationship to User
    user = relationship("User", backref="photos")

    def __repr__(self):
        return f"<Photo(photo_id='{self.photo_id}', user_id='{self.user_id}')>"
