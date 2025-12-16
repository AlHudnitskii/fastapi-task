"""Transaction API."""

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.schemas import RequestTransactionModel, TransactionModel
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "/users/{user_id}",
    response_model=TransactionModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transaction",
    description="Create a deposit (positive amount) or withdrawal (negative amount) transaction",
)
async def create_transaction(
    user_id: int,
    transaction_data: RequestTransactionModel,
    session: AsyncSession = Depends(get_async_session),
) -> TransactionModel:
    """Create a transaction."""
    service = TransactionService(session)
    return await service.create_transaction(user_id, transaction_data)


@router.get(
    "",
    response_model=List[TransactionModel],
    status_code=status.HTTP_200_OK,
    summary="Get transactions",
    description="Get list of transactions with optional user filter",
)
async def get_transactions(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
) -> List[TransactionModel]:
    """Get transactions with optional filters."""
    service = TransactionService(session)
    return await service.get_transactions(user_id=user_id, skip=skip, limit=limit)


@router.patch(
    "/users/{user_id}/transactions/{transaction_id}/rollback",
    response_model=TransactionModel,
    status_code=status.HTTP_200_OK,
    summary="Rollback a transaction",
    description="Reverse a transaction: refund withdrawals or deduct deposits",
)
async def rollback_transaction(
    user_id: int,
    transaction_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> TransactionModel:
    """Rollback a transaction."""
    service = TransactionService(session)
    return await service.rollback_transaction(user_id, transaction_id)
