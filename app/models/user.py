import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """
    User model for authentication and user management.
    Inherits common fields from BaseModel:
    - date_created, date_updated, created_by, updated_by, active, meta
    """
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    avatar_url = Column(String, nullable=True)
    fcm_token = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    
    # One-to-one relationship with Profile
    profile = relationship("Profile", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}')>"
