"""User service module."""

from typing import List, Optional

from loguru import logger
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
        self.user_repository = UserRepository(session)
        self.balance_repository = BalanceRepository(session)

    async def create_user(self, user_data: UserCreateRequest) -> UserDetailResponse:
        """Create a new user with balances for all currencies."""
        if await self.user_repository.email_exists(user_data.email):
            logger.warning("User creation failed: Email already exists", email=user_data.email)
            raise UserAlreadyExistsException(user_data.email)

        logger.info("Attempting to create new user", email=user_data.email)

        async with self.user_repository.transaction():
            user = await self.user_repository.create(
                email=user_data.email,
                status=UserStatusEnumDB.ACTIVE,
            )

            balances = await self.balance_repository.create_all_currency_balances(user.id)

            await self.session.refresh(user)

        logger.success(
            "User successfully created with initial balances",
            user_id=user.id,
            email=user_data.email,
        )

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
        filters = {
            "user_id": user_id,
            "email": email,
            "status": status.name if status else None,
        }
        logger.info(
            "Fetching users with filters",
            **{k: v for k, v in filters.items() if v is not None},
        )

        users = await self.user_repository.get_with_filters(
            user_id=user_id,
            email=email,
            status=status,
        )

        logger.info(f"Found {len(users)} users matching the criteria.")

        result = []
        for user in users:
            balances = await self.balance_repository.get_user_balances(user.id)
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
        logger.info("Fetching user details by ID", user_id=user_id)

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.warning("User not found by ID", user_id=user_id)
            raise UserNotExistsException(user_id)

        balances = await self.balance_repository.get_user_balances(user_id)

        logger.debug("Successfully fetched user and balances", user_id=user_id)

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
        new_status = update_data.status.name
        logger.info(f"Attempting to update user {user_id} status to {new_status}")

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.warning("User not found for status update", user_id=user_id)
            raise UserNotExistsException(user_id)

        old_status = user.status.name

        if old_status != new_status:
            pass
        elif update_data.status == UserStatusEnumDB.BLOCKED:
            logger.warning("Status update redundant: User already blocked", user_id=user_id)
            raise UserAlreadyBlockedException(user_id)
        else:
            logger.warning("Status update redundant: User already active", user_id=user_id)
            raise UserAlreadyActiveException(user_id)

        async with self.user_repository.transaction():
            updated_user = await self.user_repository.update(user, status=update_data.status)

        logger.success(
            "User status successfully updated",
            user_id=user_id,
            old_status=old_status,
            new_status=new_status,
        )

        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            status=updated_user.status,
            created=updated_user.created,
        )

    async def _get_user_or_raise(self, user_id: int) -> User:
        """Get user or raise exception if not found."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotExistsException(user_id)
        return user
