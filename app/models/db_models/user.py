from models.enums import CurrencyEnumDB, UserStatusEnumDB
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
        passive_deletes=True,
        lazy="selectin",
    )
    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
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
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    currency = Column(Enum(CurrencyEnumDB), nullable=False)
    amount = Column(Numeric(precision=24, scale=8), nullable=False, default=0)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="balances")

    def __repr(self) -> str:
        return f"<UserBalance(id={self.id}, user_id={self.user_id}, currency={self.currency}, amount={self.amount})>"
