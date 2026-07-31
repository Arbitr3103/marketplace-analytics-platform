"""Public API contracts."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DashboardSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    period_days: int
    stores: int
    sku_count: int
    orders: int
    revenue: float
    average_order_value: float
    stock_alerts: int
    generated_at: datetime


class SyncRequest(BaseModel):
    provider: Literal["demo", "ozon", "wildberries"] = "demo"
    date_from: date
    date_to: date

    def validate_period(self) -> None:
        if self.date_from > self.date_to:
            raise ValueError("date_from must not be later than date_to")
        if (self.date_to - self.date_from).days > 90:
            raise ValueError("sync period must not exceed 90 days")


class SyncAccepted(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    status: Literal["queued", "duplicate"]
    idempotency_key: str = Field(min_length=8, max_length=128)
