import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.db_models import (
    CurrencyEnumDB,
    TransactionStatusEnumDB,
    UserStatusEnumDB,
)


class UserCreateRequest(BaseModel):
    """Request schema for creating a user"""

    email: EmailStr = Field(..., description="User email address")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate that email is not just white"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not v or not v.strip():
            raise ValueError("Email can't be empty")

        cleaned = v.strip()

        if not re.match(pattern, cleaned):
            raise ValueError("Uncorrect email format")
        return cleaned


class UserUpdateRequest(BaseModel):
    """Request schema for updating user status"""

    status: UserStatusEnumDB = Field(..., description="New user status")


class BalanceResponse(BaseModel):
    """Response schema for user balance"""

    currency: CurrencyEnumDB
    amount: Decimal = Field(..., ge=0, description="Balance amount (non-negative)")

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: lambda v: float(v)},
    }


class UserResponse(BaseModel):
    """Response schema for user without balances"""

    id: int
    email: str
    status: UserStatusEnumDB
    created: datetime

    model_config = {"from_attributes": True}


class UserDetailResponse(UserResponse):
    """Response schema for user with balances"""

    balances: List[BalanceResponse] = Field(default_factory=list)


class RequestTransactionModel(BaseModel):
    currency: CurrencyEnumDB
    amount: float


class TransactionModel(BaseModel):
    id: typing.Optional[int]
    user_id: typing.Optional[int] = None
    currency: typing.Optional[CurrencyEnumDB] = None
    amount: typing.Optional[float] = None
    status: typing.Optional[TransactionStatusEnumDB] = None
    created: typing.Optional[datetime] = None
