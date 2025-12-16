"""Celery tasks for generating reports."""

import asyncio
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.services.report_service import ReportService
from app.tasks.celery_app import celery_app


async def generate_report(weeks: int) -> List[Dict]:
    """Generate weekly report asynchronously."""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        report_service = ReportService(session)
        report = await report_service.generate_weekly_report(weeks=weeks)

    await engine.dispose()
    return report


@celery_app.task(name="generate_weekly_report", bind=True)
def generate_weekly_report_task(self, weeks: int = 52) -> List[Dict]:
    """Celery task to generate weekly report."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(generate_report(weeks))
    return result
