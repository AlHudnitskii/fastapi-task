from datetime import datetime
from typing import Optional

from models.enums import CurrencyEnumDB, TransactionStatusEnumDB
from pydantic import BaseModel


class RequestTransactionModel(BaseModel):
    currency: CurrencyEnumDB
    amount: float


class TransactionModel(BaseModel):
    id: Optional[int]
    user_id: Optional[int] = None
    currency: Optional[CurrencyEnumDB] = None
    amount: Optional[float] = None
    status: Optional[TransactionStatusEnumDB] = None
    created: Optional[datetime] = None
