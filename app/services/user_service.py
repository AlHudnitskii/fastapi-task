"""User service module."""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    UserAlreadyActiveException,
    UserAlreadyBlockedException,
    UserAlreadyExistsException,
    UserNotExistsException,
)
from app.models.db_models import User
from app.models.enums import UserStatusEnumDB
from app.models.schemas import UserCreateRequest, UserDetailResponse, UserResponse, UserUpdateRequest
from app.repositories.balance_repository import BalanceRepository
from app.repositories.user_repository import UserRepository


class UserService:
    """Service for user operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session."""
        self.session = session
        self.user_repo = UserRepository(session)
        self.balance_repo = BalanceRepository(session)

    async def create_user(self, user_data: UserCreateRequest) -> UserDetailResponse:
        """Create a new user with balances for all currencies."""
        if await self.user_repo.email_exists(user_data.email):
            raise UserAlreadyExistsException(user_data.email)

        async with self.user_repo.transaction():
            user = await self.user_repo.create(
                email=user_data.email,
                status=UserStatusEnumDB.ACTIVE,
            )

            balances = await self.balance_repo.create_all_currency_balances(user.id)

            await self.session.refresh(user)

            return UserDetailResponse(
                id=user.id,
                email=user.email,
                status=user.status,
                created=user.created,
                balances=[{"currency": b.currency, "amount": b.amount} for b in balances],
            )

    async def get_users(
        self,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        status: Optional[UserStatusEnumDB] = None,
    ) -> List[UserDetailResponse]:
        """Get users with filters."""
        users = await self.user_repo.get_with_filters(
            user_id=user_id,
            email=email,
            status=status,
        )

        result = []
        for user in users:
            balances = await self.balance_repo.get_user_balances(user.id)
            result.append(
                UserDetailResponse(
                    id=user.id,
                    email=user.email,
                    status=user.status,
                    created=user.created,
                    balances=[{"currency": b.currency, "amount": b.amount} for b in balances],
                )
            )

        return result

    async def get_user_by_id(self, user_id: int) -> UserDetailResponse:
        """Get user by ID with balances."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotExistsException(user_id)

        balances = await self.balance_repo.get_user_balances(user.id)

        return UserDetailResponse(
            id=user.id,
            email=user.email,
            status=user.status,
            created=user.created,
            balances=[{"currency": b.currency, "amount": b.amount} for b in balances],
        )

    async def update_user_status(
        self,
        user_id: int,
        update_data: UserUpdateRequest,
    ) -> UserResponse:
        """Update user status."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotExistsException(user_id)

        if user.status == update_data.status:
            if update_data.status == UserStatusEnumDB.BLOCKED:
                raise UserAlreadyBlockedException(user_id)
            else:
                raise UserAlreadyActiveException(user_id)

        async with self.user_repo.transaction():
            updated_user = await self.user_repo.update(user, status=update_data.status)

        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            status=updated_user.status,
            created=updated_user.created,
        )

    async def _get_user_or_raise(self, user_id: int) -> User:
        """Get user or raise exception if not found."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotExistsException(user_id)
        return user
