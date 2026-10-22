import uuid
from datetime import datetime
from pydantic import  Field, EmailStr
from typing import Optional
from features.base.schema import BaseSchema


class AccessTokenResponse(BaseSchema):
    """Only the access token is returned in the body. Refresh token lives in httpOnly cookie."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseSchema):
    email: Optional[str] = None

class CreateRefreshToken(BaseSchema):
    user_id: uuid.UUID
    token: str
    expires_at: datetime

class LoginSchema(BaseSchema):
    email: EmailStr
    password: str = Field(..., max_length=128)