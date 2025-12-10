import asyncio
import logging
from datetime import datetime

from app.models.accounting_models import OutboxEvent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class OutboxProcessor:
    """Processor for pending events"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_pending_events(self, batch_size: int = 100) -> int:
        """Processes pending events"""
        result = await self.session.execute(
            select(OutboxEvent)
            .where(OutboxEvent.status == "PENDING")
            .order_by(OutboxEvent.created_at)
            .limit(batch_size)
        )
        events = result.scalars().all()

        processed_count = 0

        for event in events:
            try:
                await self._publish_event(event)

                event.status = "PROCESSED"
                event.processed_at = datetime.utcnow()
                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing event {event.id}: {str(e)}")
                event.status = "FAILED"
                event.retry_count += 1
                event.error_message = str(e)[:1000]

        await self.session.commit()
        return processed_count

    async def _publish_event(self, event: OutboxEvent):
        """Publishes an event"""
        logger.info(
            f"Publishing event: {event.event_type} "
            f"for {event.aggregate_type}:{event.aggregate_id}"
        )
        # TODO:
        await asyncio.sleep(0.1)
