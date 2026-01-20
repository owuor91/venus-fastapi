import uuid
from sqlalchemy import (
    Column, String, Boolean, Date, ForeignKey, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Profile(BaseModel):
    """
    Profile model for user profile information.
    One-to-one relationship with User.
    Inherits common fields from BaseModel:
    - date_created, date_updated, created_by, updated_by, active, meta
    """
    __tablename__ = "profiles"

    profile_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        unique=True,
        nullable=False,
        index=True
    )
    phone_number = Column(String, unique=True, nullable=False, index=True)
    # Using String to store GenderEnum value
    gender = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    bio = Column(String, nullable=False)
    online = Column(Boolean, nullable=False, default=True)
    # Format: "lat,lng" e.g. "-1.2921,36.8219"
    current_coordinates = Column(String, nullable=True)
    # Format: {"min_age": int, "max_age": int, "distance": float}
    preferences = Column(JSON, nullable=True)

    # Relationship back to User
    user = relationship("User", back_populates="profile")

    # Unique constraint on user_id and phone_number
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_profile_user_id'),
        UniqueConstraint('phone_number', name='uq_profile_phone_number'),
    )

    def __repr__(self):
        return (
            f"<Profile(profile_id='{self.profile_id}', "
            f"user_id='{self.user_id}')>"
        )
