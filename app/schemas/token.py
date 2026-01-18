from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.profile import Profile


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    first_name: str
    last_name: str
    email: str
    profile: Optional[Profile] = None


class TokenData(BaseModel):
    email: str | None = None
