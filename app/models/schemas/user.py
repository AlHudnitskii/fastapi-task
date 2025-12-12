"""User schemas module."""

import re
from datetime import datetime
from decimal import Decimal
from typing import List

from models.enums import CurrencyEnumDB, UserStatusEnumDB
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreateRequest(BaseModel):
    """Request schema for creating a user."""

    email: EmailStr = Field(..., description="User email address")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate that email is not just white."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not v or not v.strip():
            raise ValueError("Email can't be empty")

        cleaned = v.strip()

        if not re.match(pattern, cleaned):
            raise ValueError("Uncorrect email format")
        return cleaned


class UserUpdateRequest(BaseModel):
    """Request schema for updating user status."""

    status: UserStatusEnumDB = Field(..., description="New user status")


class BalanceResponse(BaseModel):
    """Response schema for user balance."""

    currency: CurrencyEnumDB
    amount: Decimal = Field(..., ge=0, description="Balance amount (non-negative)")

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: lambda v: Decimal(v)},
    }


class UserResponse(BaseModel):
    """Response schema for user without balances."""

    id: int
    email: str
    status: UserStatusEnumDB
    created: datetime

    model_config = {"from_attributes": True}


class UserDetailResponse(UserResponse):
    """Response schema for user with balances."""

    balances: List[BalanceResponse] = Field(default_factory=list)
