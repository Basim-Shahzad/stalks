from pydantic import Field, EmailStr
from typing import Optional
from .base import CamelModel


class TokenResponse(CamelModel):

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(CamelModel):
    email: Optional[str] = None


class LoginSchema(CamelModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class RefreshTokenRequest(CamelModel):
    refresh_token: str
