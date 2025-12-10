from enum import StrEnum


class CurrencyEnumDB(StrEnum):
    """Supported currencies"""

    USD = "USD"
    EUR = "EUR"
    AUD = "AUD"
    CAD = "CAD"
    ARS = "ARS"
    PLN = "PLN"
    BTC = "BTC"
    ETH = "ETH"
    DOGE = "DOGE"
    USDT = "USDT"


class EventStatusEnumDB(StrEnum):
    """Status of event"""

    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class AccountTypeEnumDB(StrEnum):
    """Supported account types"""

    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class UserStatusEnumDB(StrEnum):
    """User account status"""

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class EntryTypeEnumDB(StrEnum):
    """Type of journal entry"""

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class TransactionStatusEnumDB(StrEnum):
    """Transaction status"""

    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
