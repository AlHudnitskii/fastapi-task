"""Users API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.enums import UserStatusEnumDB
from app.models.schemas import UserCreateRequest, UserDetailResponse, UserResponse, UserUpdateRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Register a new user with automatic wallet creation for all supported currencies",
)
async def create_user(
    user_data: UserCreateRequest,
    session: AsyncSession = Depends(get_async_session),
) -> UserDetailResponse:
    """Create a new user."""
    service = UserService(session)
    return await service.create_user(user_data)


@router.get(
    "",
    response_model=List[UserDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get users",
    description="Get list of users with optional filters",
)
async def get_users(
    user_id: Optional[int] = None,
    email: Optional[str] = None,
    user_status: Optional[UserStatusEnumDB] = None,
    session: AsyncSession = Depends(get_async_session),
) -> List[UserDetailResponse]:
    """Get users with optional filters."""
    service = UserService(session)
    return await service.get_users(
        user_id=user_id,
        email=email,
        status=user_status,
    )


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="Get detailed user information including balances",
)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> UserDetailResponse:
    """Get user by ID."""
    service = UserService(session)
    return await service.get_user_by_id(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user status",
    description="Update user status (ACTIVE/BLOCKED)",
)
async def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
) -> UserResponse:
    """Update user status."""
    service = UserService(session)
    return await service.update_user_status(user_id, update_data)
