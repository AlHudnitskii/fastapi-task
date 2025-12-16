"""Repository for Transaction operations."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models.transaction import Transaction
from app.models.enums import CurrencyEnumDB, TransactionStatusEnumDB
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for Transaction operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize TransactionRepository."""
        super().__init__(Transaction, session)

    async def get_user_transactions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Transaction]:
        """Get transactions for a user."""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_transactions(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Transaction]:
        """Get all transactions."""
        result = await self.session.execute(
            select(Transaction).order_by(Transaction.created.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[TransactionStatusEnumDB] = None,
    ) -> int:
        """Count transactions in period."""
        query = (
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.created >= start_date)
            .where(Transaction.created <= end_date)
        )

        if status is not None:
            query = query.where(Transaction.status == status)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_transactions_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[TransactionStatusEnumDB] = None,
        amount_condition: Optional[str] = None,
    ) -> List[Transaction]:
        """Get transactions in period with filters."""
        query = select(Transaction).where(Transaction.created >= start_date).where(Transaction.created <= end_date)

        if status is not None:
            query = query.where(Transaction.status == status)

        if amount_condition == "positive":
            query = query.where(Transaction.amount > 0)
        elif amount_condition == "negative":
            query = query.where(Transaction.amount < 0)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def sum_amount_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
        currency: Optional[CurrencyEnumDB] = None,
        status: Optional[TransactionStatusEnumDB] = None,
        amount_condition: Optional[str] = None,
    ) -> Decimal:
        """Sum transaction amounts in period."""
        query = (
            select(func.sum(Transaction.amount))
            .where(Transaction.created >= start_date)
            .where(Transaction.created <= end_date)
        )

        if currency is not None:
            query = query.where(Transaction.currency == currency)

        if status is not None:
            query = query.where(Transaction.status == status)

        if amount_condition == "positive":
            query = query.where(Transaction.amount > 0)
        elif amount_condition == "negative":
            query = query.where(Transaction.amount < 0)

        result = await self.session.execute(query)
        total = result.scalar()

        return Decimal(str(total)) if total is not None else Decimal("0")

    async def count_users_with_deposits_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
        user_ids: List[int],
        include_rollbacked: bool = True,
    ) -> int:
        """Count users who made deposits in period."""
        query = (
            select(func.count(func.distinct(Transaction.user_id)))
            .where(Transaction.user_id.in_(user_ids))
            .where(Transaction.created >= start_date)
            .where(Transaction.created <= end_date)
            .where(Transaction.amount > 0)
        )

        if not include_rollbacked:
            query = query.where(Transaction.status == TransactionStatusEnumDB.DRAFT)

        result = await self.session.execute(query)
        return result.scalar() or 0
