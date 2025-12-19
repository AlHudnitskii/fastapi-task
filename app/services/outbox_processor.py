"""Processor for pending events."""

import asyncio
from datetime import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models.accounting import OutboxEvent


class OutboxProcessor:
    """Processor for pending events."""

    def __init__(self, session: AsyncSession):
        """Initialize the OutboxProcessor with an AsyncSession."""
        self.session = session

    async def process_pending_events(self, batch_size: int = 100) -> int:
        """Process pending events."""
        logger.info(f"Starting to process pending events (batch size: {batch_size})")

        result = await self.session.execute(
            select(OutboxEvent)
            .where(OutboxEvent.status == "PENDING")
            .order_by(OutboxEvent.created_at)
            .limit(batch_size)
        )
        events = result.scalars().all()

        logger.info(f"Found {len(events)} events to process.")

        processed_count = 0

        for event in events:
            event_logger = logger.bind(
                event_id=event.id,
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
            )

            try:
                await self._publish_event(event, event_logger)

                event.status = "PROCESSED"
                event.processed_at = datetime.utcnow()
                processed_count += 1

                event_logger.success("Event successfully processed and marked as PROCESSED.")

            except Exception as e:
                error_message = str(e)[:1000]
                event_logger.error(
                    "Error processing and publishing event.",
                    error=error_message,
                    retry_count=event.retry_count + 1,
                    exception=e,
                )

                event.status = "FAILED"
                event.retry_count += 1
                event.error_message = error_message

        await self.session.commit()

        logger.info(f"Finished processing batch. Total processed: {processed_count}/{len(events)}")

        return processed_count

    async def _publish_event(self, event: OutboxEvent, event_logger=logger):
        """Publish an event."""
        event_logger.info(f"Publishing event: {event.event_type} for {event.aggregate_type}:{event.aggregate_id}")
        await asyncio.sleep(0.1)

        event_logger.debug("Event publication simulated (asyncio.sleep)")
