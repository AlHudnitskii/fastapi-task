"""Unit tests for UserService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    UserAlreadyActiveException,
    UserAlreadyBlockedException,
    UserAlreadyExistsException,
    UserNotExistsException,
)
from app.models.enums import CurrencyEnumDB, UserStatusEnumDB
from app.models.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services.user_service import UserService


class TestUserService:
    """Test suite for UserService."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession) -> None:
        """Test successful user creation with balances."""
        service = UserService(db_session)
        user_data = UserCreateRequest(email="test@example.com")

        result = await service.create_user(user_data)

        assert result.id is not None
        assert result.email == "test@example.com"
        assert result.status == UserStatusEnumDB.ACTIVE
        assert len(result.balances) == len(CurrencyEnumDB)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, db_session: AsyncSession) -> None:
        """Test user creation with duplicate email raises exception."""
        service = UserService(db_session)
        user_data = UserCreateRequest(email="duplicate@example.com")

        await service.create_user(user_data)

        with pytest.raises(UserAlreadyExistsException) as exc_info:
            await service.create_user(user_data)

        assert "already exists" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, db_session: AsyncSession) -> None:
        """Test getting user by ID."""
        service = UserService(db_session)
        user_data = UserCreateRequest(email="get@example.com")

        created_user = await service.create_user(user_data)
        result = await service.get_user_by_id(created_user.id)

        assert result.id == created_user.id
        assert result.email == "get@example.com"
        assert len(result.balances) == len(CurrencyEnumDB)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session: AsyncSession) -> None:
        """Test getting non-existent user raises exception."""
        service = UserService(db_session)

        with pytest.raises(UserNotExistsException) as exc_info:
            await service.get_user_by_id(99999)

        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_user_status_to_blocked(self, db_session: AsyncSession) -> None:
        """Test updating user status to BLOCKED."""
        service = UserService(db_session)
        user_data = UserCreateRequest(email="block@example.com")

        created_user = await service.create_user(user_data)
        update_data = UserUpdateRequest(status=UserStatusEnumDB.BLOCKED)

        result = await service.update_user_status(created_user.id, update_data)

        assert result.status == UserStatusEnumDB.BLOCKED
        assert result.id == created_user.id

    @pytest.mark.asyncio
    async def test_update_user_status_to_active(self, db_session: AsyncSession) -> None:
        """Test updating user status from BLOCKED to ACTIVE."""
        service = UserService(db_session)
        user_data = UserCreateRequest(email="activate@example.com")

        created_user = await service.create_user(user_data)

        await service.update_user_status(created_user.id, UserUpdateRequest(status=UserStatusEnumDB.BLOCKED))

        result = await service.update_user_status(created_user.id, UserUpdateRequest(status=UserStatusEnumDB.ACTIVE))

        assert result.status == UserStatusEnumDB.ACTIVE

    @pytest.mark.asyncio
    async def test_update_user_status_already_blocked(self, db_session: AsyncSession) -> None:
        """Test updating already blocked user raises exception."""
        service = UserService(db_session)
        user_data = UserCreateRequest(email="alreadyblocked@example.com")

        created_user = await service.create_user(user_data)
        await service.update_user_status(created_user.id, UserUpdateRequest(status=UserStatusEnumDB.BLOCKED))

        with pytest.raises(UserAlreadyBlockedException) as exc_info:
            await service.update_user_status(created_user.id, UserUpdateRequest(status=UserStatusEnumDB.BLOCKED))

        assert "already blocked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_user_status_already_active(self, db_session: AsyncSession) -> None:
        """Test updating already active user raises exception."""
        service = UserService(db_session)
        user_data = UserCreateRequest(email="alreadyactive@example.com")

        created_user = await service.create_user(user_data)

        with pytest.raises(UserAlreadyActiveException) as exc_info:
            await service.update_user_status(created_user.id, UserUpdateRequest(status=UserStatusEnumDB.ACTIVE))

        assert "already active" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_user_status_not_found(self, db_session: AsyncSession) -> None:
        """Test updating non-existent user raises exception."""
        service = UserService(db_session)
        update_data = UserUpdateRequest(status=UserStatusEnumDB.BLOCKED)

        with pytest.raises(UserNotExistsException):
            await service.update_user_status(99999, update_data)
