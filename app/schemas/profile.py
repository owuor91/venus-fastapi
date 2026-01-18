from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.models.enums import GenderEnum


class ProfileBase(BaseModel):
    phone_number: str
    gender: GenderEnum
    date_of_birth: date
    bio: str
    online: bool = True


class ProfileCompletionRequest(BaseModel):
    phone_number: str
    gender: GenderEnum
    date_of_birth: date
    bio: str


class ProfileCreate(ProfileBase):
    user_id: UUID
    created_by: str
    updated_by: str


class ProfileUpdate(BaseModel):
    phone_number: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    bio: Optional[str] = None
    online: Optional[bool] = None
    updated_by: str
    meta: Optional[Dict[str, Any]] = None


class ProfileInDB(ProfileBase):
    profile_id: UUID
    user_id: UUID
    date_created: datetime
    date_updated: datetime
    created_by: str
    updated_by: str
    active: bool
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class Profile(ProfileInDB):
    pass
