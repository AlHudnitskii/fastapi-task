from optparse import Option
from typing import Generic, List, Optional, Type, TypeVar

from pydantic.main import ModelT
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with CRUD operations"""

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        """Initialize repository"""

        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get entity by ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
