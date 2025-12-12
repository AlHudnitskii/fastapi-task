from models.enums import AccountTypeEnumDB, EntryTypeEnumDB, EventStatusEnumDB
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Account(Base):
    """Account for storing financial transactions"""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    account_type = Column(
        Enum(AccountTypeEnumDB),
        nullable=False,
        default=AccountTypeEnumDB.ASSET,
        index=True,
    )
    parent_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    is_active = Column(Boolean, default=True)

    parent = relationship("Account", remote_side=[id], backref="children")
    entries = relationship(
        "JournalEntry",
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, code='{self.code}', name='{self.name}', type={self.account_type.value})>"


class JournalEntry(Base):
    """Log entry for financial transactions"""

    __tablename__ = "journal_entries"
    __table_args__ = CheckConstraint("amount > 0", name="positive_amount")

    id = Column(Integer, primary_key=True)
    transaction_id = Column(
        Integer,
        ForeignKey("transactions.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    entry_type = Column(
        Enum(EntryTypeEnumDB),
        nullable=False,
        default=EntryTypeEnumDB.DEBIT,
        index=True,
    )
    amount = Column(Numeric(19, 4), nullable=False)
    description = Column(String(500))

    transaction = relationship("Transaction", back_populates="entries")
    account = relationship("Account", back_populates="entries")

    def __repr__(self) -> str:
        return (
            f"<JournalEntry("
            f"id={self.id}, "
            f"transaction_id={self.transaction_id}, "
            f"account_id={self.account_id}, "
            f"type={self.entry_type.value if self.entry_type else 'None'}, "
            f"amount={self.amount}"
            f")>"
        )


class OutboxEvent(Base):
    """Transaction outbox event"""

    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True)
    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    created = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    processed = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    status = Column(
        Enum(EventStatusEnumDB, name="event_status_enum"),
        default=EventStatusEnumDB.PENDING,
        nullable=False,
    )
    retry_count = Column(Integer, default=0)
    error_message = Column(String(1000), nullable=True)

    transaction_id = Column(
        Integer,
        ForeignKey("transactions.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    transaction = relationship("Transaction", back_populates="outbox_event")

    def __repr__(self) -> str:
        return (
            f"<OutboxEvent("
            f"id={self.id}, "
            f"aggregate='{self.aggregate_type}:{self.aggregate_id}', "
            f"event='{self.event_type}', "
            f"status={self.status.value if self.status else 'None'}, "
            f"created={self.created}"
            f")>"
        )
