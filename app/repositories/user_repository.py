"""Repository for User operations."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models.user import User
from app.models.enums import UserStatusEnumDB
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository."""
        super().__init__(User, session)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_with_filters(
        self,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        status: Optional[UserStatusEnumDB] = None,
    ) -> List[User]:
        """Get users with filters."""
        query = select(User).order_by(User.created.desc())

        if user_id is not None:
            query = query.where(User.id == user_id)
        if email is not None:
            query = query.where(User.email == email)
        if status is not None:
            query = query.where(User.status == status)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        result = await self.session.execute(select(func.count()).select_from(User).where(User.email == email))
        count = result.scalar()
        return count > 0

    async def count_registered_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count users registered in period."""
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.created >= start_date).where(User.created <= end_date)
        )
        return result.scalar() or 0

    async def get_registered_in_period(self, start_date: datetime, end_date: datetime) -> List[User]:
        """Get users registered in period."""
        result = await self.session.execute(
            select(User).where(User.created >= start_date).where(User.created <= end_date)
        )
        return list(result.scalars().all())
