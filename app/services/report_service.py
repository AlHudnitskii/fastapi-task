"""Report Service Module."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TransactionStatusEnumDB
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository


class ReportService:
    """Report Service Class."""

    EXCHANGE_RATES_TO_USD = {
        "USD": Decimal("1.0"),
        "EUR": Decimal("0.9342"),
        "AUD": Decimal("0.5447"),
        "CAD": Decimal("0.6162"),
        "ARS": Decimal("0.0009"),
        "PLN": Decimal("0.2343"),
        "BTC": Decimal("100000.0"),
        "ETH": Decimal("3557.3476"),
        "DOGE": Decimal("0.3627"),
        "USDT": Decimal("0.9709"),
    }

    def __init__(self, session: AsyncSession):
        """Initialize ReportService with an AsyncSession."""
        self.session = session
        self.user_repository = UserRepository(session)
        self.transaction_repository = TransactionRepository(session)

    async def generate_weekly_report(self, weeks: int = 52) -> List[Dict]:
        """Generate weekly transaction analysis report for the last N weeks (by default : 52)."""
        logger.info(f"Starting weekly report generation for last {weeks} weeks.")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=6)

        reports = []
        weeks_with_activity = 0

        for i in range(weeks):
            week_start_str = start_date.date().isoformat()
            week_end_str = end_date.date().isoformat()

            report_logger = logger.bind(week_number=i + 1, start_date=week_start_str, end_date=week_end_str)
            report_logger.debug(
                f"Generating report for week {i + 1}/{weeks}. Period: {week_start_str} - {week_end_str}"
            )

            report = await self._generate_weekly_report(start_date, end_date)

            if self._has_activity(report):
                reports.append(report)
                weeks_with_activity += 1
                report_logger.info("Report generated with activity.")
            else:
                report_logger.debug("Report generated, but no activity found. Skipping.")

            end_date = start_date - timedelta(days=7)
            start_date -= timedelta(days=7)

        logger.info(f"Finished weekly report generation. Found {weeks_with_activity} weeks with activity.")
        return reports

    async def _generate_weekly_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """Protected method to generate a weekly report."""
        registered_users = await self.user_repository.get_registered_in_period(start_date, end_date)
        registered_users_count = len(registered_users)
        user_ids = [user.id for user in registered_users]

        deposits_all = await self.transaction_repository.get_transactions_in_period(
            start_date,
            end_date,
            amount_condition="positive",
        )

        deposits_posted = await self.transaction_repository.get_transactions_in_period(
            start_date=start_date,
            end_date=end_date,
            status=TransactionStatusEnumDB.POSTED,
            amount_condition="positive",
        )

        withdrawals_posted = await self.transaction_repository.get_transactions_in_period(
            start_date=start_date,
            end_date=end_date,
            status=TransactionStatusEnumDB.POSTED,
            amount_condition="negative",
        )

        all_transactions = await self.transaction_repository.get_transactions_in_period(
            start_date=start_date,
            end_date=end_date,
        )

        posted_transactions = await self.transaction_repository.get_transactions_in_period(
            start_date=start_date,
            end_date=end_date,
            status=TransactionStatusEnumDB.POSTED,
        )

        users_with_deposits_all = len(set(t.user_id for t in deposits_all if t.user_id in user_ids))
        users_with_deposits_posted = len(set(t.user_id for t in deposits_posted if t.user_id in user_ids))
        users_with_withdrawals_posted = len(set(t.user_id for t in withdrawals_posted if t.user_id in user_ids))

        total_deposits_usd = sum(self._convert_to_usd(t.amount, str(t.currency)) for t in deposits_posted)
        total_withdrawals_usd = abs(sum(self._convert_to_usd(t.amount, str(t.currency)) for t in withdrawals_posted))

        return {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "registered_users_count": registered_users_count,
            "users_with_deposits_count": users_with_deposits_all,
            "users_with_posted_deposits_count": users_with_deposits_posted,
            "users_with_posted_withdrawals_count": users_with_withdrawals_posted,
            "total_deposits_usd": float(total_deposits_usd),
            "total_withdrawals_usd": float(total_withdrawals_usd),
            "total_transactions_count": len(all_transactions),
            "posted_transactions_count": len(posted_transactions),
        }

    def _convert_to_usd(self, amount: Decimal, currency: str) -> Decimal:
        """Protected method to convert an amount to USD."""
        rate = self.EXCHANGE_RATES_TO_USD.get(currency, Decimal("1.0"))
        return amount * rate

    def _has_activity(self, report: Dict) -> bool:
        """Check if report has any activity."""
        return any(
            [
                report["registered_users_count"] > 0,
                report["users_with_deposits_count"] > 0,
                report["total_transactions_count"] > 0,
            ]
        )
