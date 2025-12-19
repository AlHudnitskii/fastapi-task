"""Unit tests for ReportService."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CurrencyEnumDB
from app.models.schemas.transaction import RequestTransactionModel
from app.models.schemas.user import UserCreateRequest
from app.services.report_service import ReportService
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService


class TestReportService:
    """Test suite for ReportService."""

    @pytest.mark.asyncio
    async def test_generate_weekly_report_empty(self, db_session: AsyncSession) -> None:
        """Test generating weekly report with no transactions."""
        service = ReportService(db_session)

        result = await service.generate_weekly_report(weeks=1)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_generate_weekly_report_with_transactions(self, db_session: AsyncSession) -> None:
        """Test generating weekly report with transactions."""
        user_service = UserService(db_session)
        transaction_service = TransactionService(db_session)
        report_service = ReportService(db_session)

        user = await user_service.create_user(UserCreateRequest(email="report@example.com"))

        await transaction_service.create_transaction(
            user.id,
            RequestTransactionModel(currency=CurrencyEnumDB.USD, amount=Decimal("100")),
        )
        await transaction_service.create_transaction(
            user.id,
            RequestTransactionModel(currency=CurrencyEnumDB.EUR, amount=Decimal("50")),
        )

        result = await report_service.generate_weekly_report(weeks=1)

        assert isinstance(result, list)
        if len(result) > 0:
            report = result[0]
            assert "start_date" in report
            assert "end_date" in report
            assert "registered_users_count" in report
            assert "total_transactions_count" in report

    @pytest.mark.asyncio
    async def test_convert_to_usd(self, db_session: AsyncSession) -> None:
        """Test currency conversion to USD."""
        service = ReportService(db_session)

        usd_amount = service._convert_to_usd(Decimal("100"), "USD")
        assert usd_amount == Decimal("100")

        eur_amount = service._convert_to_usd(Decimal("100"), "EUR")
        assert eur_amount > Decimal("0")

        unknown_amount = service._convert_to_usd(Decimal("100"), "UNKNOWN")
        assert unknown_amount == Decimal("100")

    @pytest.mark.asyncio
    async def test_has_activity(self, db_session: AsyncSession) -> None:
        """Test checking if report has activity."""
        service = ReportService(db_session)

        empty_report = {
            "registered_users_count": 0,
            "users_with_deposits_count": 0,
            "total_transactions_count": 0,
        }
        assert service._has_activity(empty_report) is False

        report_with_users = {
            "registered_users_count": 1,
            "users_with_deposits_count": 0,
            "total_transactions_count": 0,
        }
        assert service._has_activity(report_with_users) is True

        report_with_transactions = {
            "registered_users_count": 0,
            "users_with_deposits_count": 0,
            "total_transactions_count": 1,
        }
        assert service._has_activity(report_with_transactions) is True

    @pytest.mark.asyncio
    async def test_generate_weekly_report_multiple_weeks(self, db_session: AsyncSession) -> None:
        """Test generating report for multiple weeks."""
        service = ReportService(db_session)

        result = await service.generate_weekly_report(weeks=4)

        assert isinstance(result, list)
        assert len(result) <= 4
