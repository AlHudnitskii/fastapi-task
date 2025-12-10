from contextlib import asynccontextmanager
from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with CRUD operations and transaction management"""

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    @asynccontextmanager
    async def transaction(self):
        """Context manager for managing transactions. Automatically commits on success, rolls back on error"""
        try:
            yield self
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise e
        finally:
            await self.session.flush()

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get entity by ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
    ) -> List[ModelType]:
        """Get all entities with pagination"""
        query = select(self.model).offset(skip).limit(limit)

        if order_by:
            query = query.order_by(getattr(self.model, order_by))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """Create new entity"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        """Update entity"""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete entity"""
        await self.session.delete(instance)
        await self.session.flush()

    async def _flush(self) -> None:
        """Flush changes to database"""
        await self.session.flush()

    async def _refresh(self, instance):
        """Refresh instance from database"""
        await self.session.refresh(instance)
