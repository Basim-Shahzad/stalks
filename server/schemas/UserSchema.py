from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import uuid


class UserBase(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    email: EmailStr = Field(max_length=255)
    is_active: bool = True


class UserCreateSchema(UserBase):
    password: str = Field(min_length=8)


class UserUpdateSchema(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8)


class UserResponseSchema(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
