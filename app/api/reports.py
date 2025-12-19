"""Reports API endpoints."""

from typing import Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.services.report_service import ReportService
from app.tasks.report_tasks import generate_weekly_report_task

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/weekly",
    response_model=List[Dict],
    status_code=status.HTTP_200_OK,
    summary="Get weekly report (synchronous)",
    description="Generate and return weekly transaction analysis for the last 52 weeks",
)
async def get_weekly_report(
    weeks: int = 52,
    session: AsyncSession = Depends(get_async_session),
) -> List[Dict]:
    """Get weekly transaction analysis report."""
    service = ReportService(session)
    return await service.generate_weekly_report(weeks=weeks)


@router.post(
    "/weekly/async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate weekly report (asynchronous)",
    description="Trigger background task to generate weekly report. Use Celery for production.",
)
async def generate_weekly_report_async(
    weeks: int = 52,
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Dict:
    """Trigger async report generation."""
    task = generate_weekly_report_task.delay(weeks)
    return {
        "message": "Report generation started",
        "task_id": task.id,
        "status": "PENDING",
    }
