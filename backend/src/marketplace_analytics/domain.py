"""Domain data and ports used by the application service."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AggregatedMetrics:
    stores: int
    sku_count: int
    orders: int
    revenue: float
    stock_alerts: int
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class SyncJob:
    provider: str
    date_from: date
    date_to: date
    requested_at: datetime


@dataclass(frozen=True, slots=True)
class QueueResult:
    job_id: str
    duplicate: bool


class AnalyticsRepository(Protocol):
    async def aggregate(self, *, days: int) -> AggregatedMetrics: ...


class SummaryCache(Protocol):
    async def get(self, key: str) -> AggregatedMetrics | None: ...

    async def set(self, key: str, value: AggregatedMetrics, *, ttl_seconds: int) -> None: ...


class SyncQueue(Protocol):
    async def enqueue(self, job: SyncJob, *, idempotency_key: str) -> QueueResult: ...
