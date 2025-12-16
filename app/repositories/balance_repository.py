"""User balance repository."""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NegativeBalanceException
from app.models.db_models import UserBalance
from app.models.enums import CurrencyEnumDB
from app.repositories.base import BaseRepository


class BalanceRepository(BaseRepository[UserBalance]):
    """Repository for UserBalance operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository."""
        super().__init__(UserBalance, session)

    async def get_by_user_and_currency(
        self,
        user_id: int,
        currency: CurrencyEnumDB,
    ) -> Optional[UserBalance]:
        """Get balance by user and currency."""
        result = await self.session.execute(
            select(UserBalance).where(UserBalance.user_id == user_id).where(UserBalance.currency == currency)
        )
        return result.scalar_one_or_none()

    async def get_user_balances(self, user_id: int) -> List[UserBalance]:
        """Get all balances for a user."""
        result = await self.session.execute(
            select(UserBalance).where(UserBalance.user_id == user_id).order_by(UserBalance.currency)
        )
        return list(result.scalars().all())

    async def update_balance(
        self,
        user_id: int,
        currency: CurrencyEnumDB,
        amount_delta: Decimal,
    ) -> UserBalance:
        """Update balance by adding delta to current amount."""
        balance = await self.get_by_user_and_currency(user_id, currency)

        if balance is None:
            raise ValueError(f"Balance not found for user {user_id} and currency {currency}")

        new_amount = balance.amount + amount_delta

        if new_amount < 0:
            raise NegativeBalanceException(
                f"Insufficient balance: current={balance.amount}, delta={amount_delta}, result={new_amount}"
            )

        balance.amount = new_amount
        await self.session.flush()
        await self.session.refresh(balance)

        return balance

    async def create_all_currency_balances(self, user_id: int) -> List[UserBalance]:
        """Create zero balances for all currencies for a user."""
        balances = []

        for currency in CurrencyEnumDB:
            balance = UserBalance(
                user_id=user_id,
                currency=currency,
                amount=Decimal("0"),
            )
            self.session.add(balance)
            balances.append(balance)

        await self.session.flush()

        for balance in balances:
            await self.session.refresh(balance)

        return balances
