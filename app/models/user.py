from sqlalchemy import Column, String

from app.models.base import BaseModel


class User(BaseModel):
    """
    User model for authentication and user management.
    Inherits common fields from BaseModel:
    - date_created, date_updated, created_by, updated_by, active, meta
    """
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    def __repr__(self):
        return f"<User(email='{self.email}')>"
