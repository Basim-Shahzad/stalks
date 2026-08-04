from datetime import datetime
from pydantic import Field, EmailStr
import uuid
from typing import Optional
from features.base.schema import BaseSchema


class UserBase(BaseSchema):

    name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr = Field(..., max_length=255)
    is_active: bool = True


class UserCreateSchema(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdateSchema(BaseSchema):
    # Fields are optional for PATCH requests
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserResponseSchema(UserBase):

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserUpdateResponseSchema(UserResponseSchema):
    """Returned after updating the current user's profile/password."""


class UserPublicResponse(BaseSchema):
    """Minimal view for public profiles"""

    id: uuid.UUID
    name: str
