from datetime import datetime
from pydantic import Field, EmailStr
import uuid
from typing import Optional
from .base import Base


class UserBase(Base):

    name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr = Field(..., max_length=255)
    is_active: bool = True


class UserCreateSchema(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdateSchema(Base):
    # Fields are optional for PATCH requests
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserResponseSchema(UserBase):

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserPublicResponse(Base):
    """Minimal view for public profiles"""

    id: uuid.UUID
    name: str
