"""Accounting repository module."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models.accounting import Account, JournalEntry, OutboxEvent
from app.models.db_models.transaction import Transaction


class AccountingRepository:
    """Repository for accounting operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with an AsyncSession."""
        self.session = session

    async def create_transaction_with_entries(
        self,
        description: str,
        entries_data: List[dict],
        reference_number: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Transaction:
        """Create a transaction with journal entries, checking the double-entry rule."""
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for entry in entries_data:
            amount = Decimal(str(entry["amount"]))
            if entry["entry_type"] == "DEBIT":
                total_debit += amount
            elif entry["entry_type"] == "CREDIT":
                total_credit += amount

        if total_debit != total_credit:
            raise ValueError(f"Rule violation: " f"Debit ({total_debit}) does not equal Credit ({total_credit})")

        transaction = Transaction(
            description=description,
            reference_number=reference_number,
            created_by=created_by,
            status="DRAFT",
        )
        self.session.add(transaction)
        await self.session.flush()

        for entry_data in entries_data:
            entry = JournalEntry(
                transaction_id=transaction.id,
                account_id=entry_data["account_id"],
                entry_type=entry_data["entry_type"],
                amount=Decimal(str(entry_data["amount"])),
                description=entry_data.get("description"),
            )
            self.session.add(entry)

        return transaction

    async def post_transaction(self, transaction_id: int) -> Transaction:
        """Post a transaction and creates an event in the outbox."""
        result = await self.session.execute(select(Transaction).where(Transaction.id == transaction_id))
        transaction = result.scalar_one()

        if transaction.status != "DRAFT":
            raise ValueError(f"Transaction already has status {transaction.status}")

        transaction.status = "POSTED"
        transaction.posted_at = datetime.utcnow()

        outbox_event = OutboxEvent(
            aggregate_type="Transaction",
            aggregate_id=str(transaction.id),
            event_type="TransactionPosted",
            payload={
                "transaction_id": transaction.id,
                "reference_number": transaction.reference_number,
                "description": transaction.description,
                "total_amount": Decimal(sum(e.amount for e in transaction.entries if e.entry_type == "DEBIT")),
                "posted_at": transaction.posted_at.isoformat(),
            },
            transaction_id=transaction.id,
        )
        self.session.add(outbox_event)

        await self.session.commit()
        return transaction

    async def get_account_balance(self, account_id: int, as_of_date: Optional[datetime] = None) -> Decimal:
        """Get the balance of an account on a specific date."""
        query = (
            select(
                func.sum(
                    func.case(
                        (JournalEntry.entry_type == "DEBIT", JournalEntry.amount),
                        else_=-JournalEntry.amount,
                    )
                )
            )
            .join(Transaction)
            .where(JournalEntry.account_id == account_id, Transaction.status == "POSTED")
        )

        if as_of_date:
            query = query.where(Transaction.posted_at <= as_of_date)

        result = await self.session.execute(query)
        balance = result.scalar()
        return balance or Decimal("0")

    async def get_trial_balance(self, as_of_date: Optional[datetime] = None) -> List[dict]:
        """Get trial balance."""
        query = (
            select(
                Account.id,
                Account.code,
                Account.name,
                Account.account_type,
                func.sum(
                    func.case(
                        (JournalEntry.entry_type == "DEBIT", JournalEntry.amount),
                        else_=0,
                    )
                ).label("total_debit"),
                func.sum(
                    func.case(
                        (JournalEntry.entry_type == "CREDIT", JournalEntry.amount),
                        else_=0,
                    )
                ).label("total_credit"),
            )
            .join(JournalEntry, JournalEntry.account_id == Account.id)
            .join(Transaction, Transaction.id == JournalEntry.transaction_id)
            .where(Transaction.status == "POSTED")
            .group_by(Account.id, Account.code, Account.name, Account.account_type)
        )

        if as_of_date:
            query = query.where(Transaction.posted_at <= as_of_date)

        result = await self.session.execute(query)

        trial_balance = []
        for row in result:
            balance = row.total_debit - row.total_credit
            trial_balance.append(
                {
                    "account_id": row.id,
                    "account_code": row.code,
                    "account_name": row.name,
                    "account_type": row.account_type,
                    "debit": Decimal(row.total_debit),
                    "credit": Decimal(row.total_credit),
                    "balance": Decimal(balance),
                }
            )

        return trial_balance
