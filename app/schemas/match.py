from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel


class MatchBase(BaseModel):
    my_id: UUID
    partner_id: UUID
    thread_id: UUID
    last_message: Optional[str] = None
    last_message_date: Optional[datetime] = None
    sent_by: Optional[UUID] = None


class MatchCreateRequest(BaseModel):
    """Request schema for creating/updating a match."""
    my_id: UUID
    partner_id: UUID
    thread_id: UUID
    last_message: Optional[str] = None
    last_message_date: Optional[datetime] = None
    sent_by: Optional[UUID] = None


class MatchCreate(MatchBase):
    created_by: str
    updated_by: str


class MatchUpdate(BaseModel):
    my_id: Optional[UUID] = None
    partner_id: Optional[UUID] = None
    thread_id: Optional[UUID] = None
    last_message: Optional[str] = None
    last_message_date: Optional[datetime] = None
    sent_by: Optional[UUID] = None
    updated_by: str
    active: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


class MatchInDB(MatchBase):
    match_id: UUID
    date_created: datetime
    date_updated: datetime
    created_by: str
    updated_by: str
    active: bool
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class Match(MatchInDB):
    pass
