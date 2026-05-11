from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import uuid
from typing import Optional


class UserBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr = Field(..., max_length=255)
    is_active: bool = True


class UserCreateSchema(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdateSchema(BaseModel):
    # Fields are optional for PATCH requests
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserResponseSchema(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserPublicResponse(BaseModel):
    """Minimal view for public profiles"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
