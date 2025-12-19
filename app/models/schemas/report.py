"""Module containing schemas for reports."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class WeeklyReport(BaseModel):
    """Weekly report schema."""

    start_date: date = Field(..., description="Start date of the report period")
    end_date: date = Field(..., description="End date of the report period")

    registered_users_count: int = Field(..., ge=0)
    users_with_deposits_count: int = Field(..., ge=0)
    users_with_posted_deposits_count: int = Field(..., ge=0)
    users_with_posted_withdrawals_count: int = Field(..., ge=0)

    total_deposits_usd: Decimal = Field(..., ge=0)
    total_withdrawals_usd: Decimal = Field(..., ge=0)

    total_transactions_count: int = Field(..., ge=0)
    posted_transactions_count: int = Field(..., ge=0)

    class Config:
        """Weekly report schema configuration."""

        from_attributes = True
