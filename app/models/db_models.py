from enum import StrEnum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


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


class UserStatusEnumDB(StrEnum):
    """User account status"""

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class TransactionStatusEnumDB(StrEnum):
    """Transaction status"""

    PROCESSED = "PROCESSED"
    ROLLBACKED = "ROLLBACKED"


class User(Base):
    """User model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(
        Enum(UserStatusEnumDB),
        nullable=False,
        default=UserStatusEnumDB.ACTIVE,
        index=True,
    )
    created = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    balances = relationship(
        "UserBalance",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, status={self.status})>"


class UserBalance(Base):
    """User balance per currency"""

    __tablename__ = "user_balances"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "currency", name="unique_user_balance_user_currency"
        ),
        Index("index_user_balances_user_currency", "user_id", "currency"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    currency = Column(Enum(CurrencyEnumDB), nullable=False)
    amount = Column(Numeric(precision=24, scale=8), nullable=False, default=0)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="balances")

    def __repr(self) -> str:
        return f"<UserBalance(id={self.id}, user_id={self.user_id}, currency={self.currency}, amount={self.amount})>"


class Transaction(Base):
    """Transaction model"""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("index_transactions_user_created", "user_id", "created"),
        Index("index_transactions_status_created", "status", "created"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    currency = Column(Enum(CurrencyEnumDB), nullable=False, index=True)
    amount = Column(Numeric(precision=24, scale=8), nullable=False)
    status = Column(
        Enum(TransactionStatusEnumDB),
        nullable=False,
        default=TransactionStatusEnumDB.PROCESSED,
        index=True,
    )
    created = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    user = relationship("User", back_populations="transactions")

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, user_id={self.user_id}, "
            f"currency={self.currency}, amount={self.amount}, status={self.status})>"
        )
