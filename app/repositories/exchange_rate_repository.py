"""Repository for working with exchange rates in the database."""

# from datetime import datetime
# from decimal import Decimal
# from typing import Dict, Optional

# from app.models.db_models.accounting import ExchangeRate
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession


# class ExchangeRateRepository:
#     """Repository for working with exchange rates in the database."""

#     def __init__(self, session: AsyncSession):
#         self.session = session

#     async def get_all_to_usd(self) -> Dict[str, Decimal]:
#         """Get all rates to USD from database."""
#         query = select(ExchangeRate).where(ExchangeRate.to_currency == "USD")
#         result = await self.session.execute(query)
#         rates = result.scalars().all()

#         return {rate.from_currency: Decimal(str(rate.rate)) for rate in rates}

#     async def get_rate(
#         self, from_currency: str, to_currency: str = "USD"
#     ) -> Optional[ExchangeRate]:
#         """Get rate from database."""
#         query = select(ExchangeRate).where(
#             ExchangeRate.from_currency == from_currency,
#             ExchangeRate.to_currency == to_currency,
#         )
#         result = await self.session.execute(query)
#         return result.scalar_one_or_none()

#     async def get_rate_value(
#         self, from_currency: str, to_currency: str = "USD"
#     ) -> Optional[Decimal]:
#         """Get rate value from database."""
#         rate = await self.get_rate(from_currency, to_currency)
#         if rate:
#             return Decimal(str(rate.rate))
#         return None

#     async def create_or_update_rate(
#         self,
#         from_currency: str,
#         rate: Decimal,
#         to_currency: str = "USD",
#         source: str = "database",
#     ) -> ExchangeRate:
#         """Create or update rate in database."""
#         existing = await self.get_rate(from_currency, to_currency)

#         if existing:
#             existing.rate = rate
#             existing.source = source
#             existing.updated_at = datetime.utcnow()
#         else:
#             existing = ExchangeRate(
#                 from_currency=from_currency,
#                 to_currency=to_currency,
#                 rate=rate,
#                 source=source,
#             )
#             self.session.add(existing)

#         return existing

#     async def bulk_create_or_update(
#         self,
#         rates: Dict[str, Decimal],
#         to_currency: str = "USD",
#         source: str = "database",
#     ) -> None:
#         """Massive create or update rates."""
#         for from_currency, rate in rates.items():
#             await self.create_or_update_rate(from_currency, rate, to_currency, source)

#     async def delete_rate(self, from_currency: str, to_currency: str = "USD") -> bool:
#         """Delete rate from database."""
#         rate = await self.get_rate(from_currency, to_currency)
#         if rate:
#             await self.session.delete(rate)
#             return True
#         return False
