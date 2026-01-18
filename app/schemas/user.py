from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str


class RegisterRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreate(UserBase):
    password: str
    avatar_url: Optional[str] = None
    fcm_token: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    fcm_token: Optional[str] = None
    updated_by: str
    active: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


class UserInDB(UserBase):
    user_id: UUID
    avatar_url: Optional[str] = None
    fcm_token: Optional[str] = None
    date_created: datetime
    date_updated: datetime
    created_by: str
    updated_by: str
    active: bool
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    pass
