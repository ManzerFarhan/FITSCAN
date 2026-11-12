from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ResetRequestIn(BaseModel):
    email: EmailStr


class ResetConfirmIn(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    phone: str | None
    dob: date | None
    gender: str | None
    preferred_city: str | None
    address: str | None
    retention_days: int | None
    height_cm: float | None = None
    weight_kg: float | None = None
    created_at: datetime


class SessionOut(BaseModel):
    authenticated: bool
    user: UserOut | None = None
    migrated_documents: int = 0


class ProfilePatch(BaseModel):
    full_name: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=32)
    dob: date | None = None
    gender: str | None = Field(None, max_length=32)
    preferred_city: str | None = Field(None, max_length=120)
    address: str | None = Field(None, max_length=500)
    retention_days: int | None = Field(None, ge=1, le=3650)
    height_cm: float | None = Field(None, ge=50, le=250)   # optional, for BMI
    weight_kg: float | None = Field(None, ge=10, le=350)   # optional, for BMI
    email: EmailStr | None = None
    current_password: str | None = None  # required to change email


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class AccountDeleteIn(BaseModel):
    password: str
