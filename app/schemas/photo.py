from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel


class PhotoBase(BaseModel):
    photo_url: str
    verified: bool = False


class PhotoCreate(PhotoBase):
    user_id: UUID
    created_by: str
    updated_by: str


class PhotoUpdate(BaseModel):
    verified: Optional[bool] = None
    updated_by: str
    active: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


class PhotoInDB(PhotoBase):
    photo_id: UUID
    user_id: UUID
    date_created: datetime
    date_updated: datetime
    created_by: str
    updated_by: str
    active: bool
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class Photo(PhotoInDB):
    pass
