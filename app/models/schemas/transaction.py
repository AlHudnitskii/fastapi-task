"""Transaction schemas module."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from models.enums import CurrencyEnumDB, TransactionStatusEnumDB
from pydantic import BaseModel


class RequestTransactionModel(BaseModel):
    """Request model for creating a transaction."""

    currency: CurrencyEnumDB
    amount: Decimal


class TransactionModel(BaseModel):
    """Model for a transaction."""

    id: Optional[int]
    user_id: Optional[int] = None
    currency: Optional[CurrencyEnumDB] = None
    amount: Optional[Decimal] = None
    status: Optional[TransactionStatusEnumDB] = None
    created: Optional[datetime] = None
