"""Unit tests for TransactionService."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NegativeBalanceException, TransactionNotFound, UserBlockedException, UserNotExistsException
from app.models.enums import CurrencyEnumDB, TransactionStatusEnumDB, UserStatusEnumDB
from app.models.schemas.transaction import RequestTransactionModel
from app.models.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService


class TestTransactionService:
    """Test suite for TransactionService."""

    @pytest.mark.asyncio
    async def test_create_deposit_transaction_success(self, db_session: AsyncSession) -> None:
        """Test successful deposit transaction creation."""
        user_service = UserService(db_session)
        transaction_service = TransactionService(db_session)

        user = await user_service.create_user(UserCreateRequest(email="deposit@example.com"))
        transaction_data = RequestTransactionModel(currency=CurrencyEnumDB.USD, amount=Decimal("100.50"))

        result = await transaction_service.create_transaction(user.id, transaction_data)

        assert result.id is not None
        assert result.user_id == user.id
        assert result.currency == CurrencyEnumDB.USD
        assert result.amount == Decimal("100.50")
        assert result.status == TransactionStatusEnumDB.POSTED

    @pytest.mark.asyncio
    async def test_create_withdrawal_transaction_success(self, db_session: AsyncSession) -> None:
        """Test successful withdrawal transaction creation."""
        user_service = UserService(db_session)
        transaction_service = TransactionService(db_session)

        user = await user_service.create_user(UserCreateRequest(email="withdraw@example.com"))

        await transaction_service.create_transaction(
            user.id,
            RequestTransactionModel(currency=CurrencyEnumDB.USD, amount=Decimal("200")),
        )

        transaction_data = RequestTransactionModel(currency=CurrencyEnumDB.USD, amount=Decimal("-50.25"))
        result = await transaction_service.create_transaction(user.id, transaction_data)

        assert result.amount == Decimal("-50.25")
        assert result.status == TransactionStatusEnumDB.POSTED

    @pytest.mark.asyncio
    async def test_create_transaction_user_not_found(self, db_session: AsyncSession) -> None:
        """Test creating transaction for non-existent user raises exception."""
        transaction_service = TransactionService(db_session)
        transaction_data = RequestTransactionModel(currency=CurrencyEnumDB.USD, amount=Decimal("100"))

        with pytest.raises(UserNotExistsException):
            await transaction_service.create_transaction(99999, transaction_data)

    @pytest.mark.asyncio
    async def test_create_transaction_user_blocked(self, db_session: AsyncSession) -> None:
        """Test creating transaction for blocked user raises exception."""
        user_service = UserService(db_session)
        transaction_service = TransactionService(db_session)

        user = await user_service.create_user(UserCreateRequest(email="blocked@example.com"))
        await user_service.update_user_status(user.id, UserUpdateRequest(status=UserStatusEnumDB.BLOCKED))

        transaction_data = RequestTransactionModel(currency=CurrencyEnumDB.USD, amount=Decimal("100"))

        with pytest.raises(UserBlockedException) as exc_info:
            await transaction_service.create_transaction(user.id, transaction_data)

        assert "blocked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_create_transaction_negative_balance(self, db_session: AsyncSession) -> None:
        """Test creating transaction that would result in negative balance raises exception."""
        user_service = UserService(db_session)
        transaction_service = TransactionService(db_session)

        user = await user_service.create_user(UserCreateRequest(email="negative@example.com"))
        transaction_data = RequestTransactionModel(currency=CurrencyEnumDB.USD, amount=Decimal("-100"))

        with pytest.raises(NegativeBalanceException) as exc_info:
            await transaction_service.create_transaction(user.id, transaction_data)

        assert "insufficient" in exc_info.value.detail.lower() or "balance" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_transactions_all(self, db_session: AsyncSession) -> None:
        """Test getting all transactions."""
        user_service = UserService(db_session)
        transaction_service = TransactionService(db_session)

        user1 = await user_service.create_user(UserCreateRequest(email="user1@example.com"))
        user2 = await user_service.create_user(UserCreateRequest(email="user2@example.com"))

        await transaction_service.create_transaction(
            user1.id,
            RequestTransactionModel(currency=CurrencyEnumDB.USD, amount=Decimal("100")),
        )
        await transaction_service.create_transaction(
            user2.id,
            RequestTransactionModel(currency=CurrencyEnumDB.EUR, amount=Decimal("50")),
        )

        results = await transaction_service.get_transactions()

        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_get_transactions_by_user(self, db_session: AsyncSession) -> None:
        """Test getting transactions filtered by user."""
        user_service = UserService(db_session)
        transaction_service = TransactionService(db_session)

        user1 = await user_service.create_user(UserCreateRequest(email="filter1@example.com"))
        user2 = await user_service.create_user(UserCreateRequest(email="filter2@example.com"))

        await transaction_service.create_transaction(
            user1.id,
            RequestTransactionModel(currency=CurrencyEnumDB.USD, amount=Decimal("100")),
        )
        await transaction_service.create_transaction(
            user2.id,
            RequestTransactionModel(currency=CurrencyEnumDB.EUR, amount=Decimal("50")),
        )

        results = await transaction_service.get_transactions(user_id=user1.id)

        assert len(results) == 1
        assert results[0].user_id == user1.id

    @pytest.mark.asyncio
    async def test_rollback_transaction_user_not_found(self, db_session: AsyncSession) -> None:
        """Test rolling back transaction for non-existent user raises exception."""
        transaction_service = TransactionService(db_session)

        with pytest.raises(UserNotExistsException):
            await transaction_service.rollback_transaction(99999, 1)

    @pytest.mark.asyncio
    async def test_rollback_transaction_not_found(self, db_session: AsyncSession) -> None:
        """Test rolling back non-existent transaction raises exception."""
        user_service = UserService(db_session)
        transaction_service = TransactionService(db_session)

        user = await user_service.create_user(UserCreateRequest(email="notfound@example.com"))

        with pytest.raises(TransactionNotFound):
            await transaction_service.rollback_transaction(user.id, 99999)
