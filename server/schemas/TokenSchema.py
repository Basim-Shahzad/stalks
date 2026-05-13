from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from .base import Base


class AccessTokenResponse(Base):
    """Only the access token is returned in the body. Refresh token lives in httpOnly cookie."""
    access_token: str
    token_type: str = "bearer"


class TokenData(Base):
    email: Optional[str] = None


class LoginSchema(Base):
    email: EmailStr
    password: str = Field(..., min_length=8)