from datetime import datetime
from pydantic import Field, EmailStr
import uuid
from typing import Optional
from .base import CamelModel


class UserBase(CamelModel):

    name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr = Field(..., max_length=255)
    is_active: bool = True


class UserCreateSchema(CamelModel):
    password: str = Field(..., min_length=8)


class UserUpdateSchema(CamelModel):
    # Fields are optional for PATCH requests
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserResponseSchema(CamelModel):

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserPublicResponse(CamelModel):
    """Minimal view for public profiles"""

    id: uuid.UUID
    name: str
