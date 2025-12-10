from models.enums import CurrencyEnumDB, TransactionStatusEnumDB
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):
    """Transaction model"""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("index_transactions_user_created", "user_id", "created"),
        Index("index_transactions_status_created", "status", "created"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    currency = Column(Enum(CurrencyEnumDB), nullable=False, index=True)
    amount = Column(Numeric(precision=24, scale=8), nullable=False)
    status = Column(
        Enum(TransactionStatusEnumDB),
        nullable=False,
        default=TransactionStatusEnumDB.DRAFT,
        index=True,
    )
    created = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user = relationship("User", back_populates="transactions")

    entries = relationship(
        "JournalEntry",
        back_populates="transaction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    outbox_event = relationship(
        "OutboxEvent",
        back_populates="transaction",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, user_id={self.user_id}, "
            f"currency={self.currency}, amount={self.amount}, status={self.status})>"
        )
