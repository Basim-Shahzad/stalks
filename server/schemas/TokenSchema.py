from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class RefreshTokenRequest(BaseModel):
    refresh_token: str
