"""Deterministic in-memory adapters used for local demo and tests."""

from datetime import UTC, datetime
from uuid import uuid4

from marketplace_analytics.domain import AggregatedMetrics, QueueResult, SyncJob


class InMemoryAnalyticsRepository:
    def __init__(self) -> None:
        self.aggregate_calls = 0

    async def aggregate(self, *, days: int) -> AggregatedMetrics:
        self.aggregate_calls += 1
        scale = days / 30
        return AggregatedMetrics(
            stores=50,
            sku_count=30_428,
            orders=round(8_420 * scale),
            revenue=round(16_840_000.0 * scale, 2),
            stock_alerts=37,
            generated_at=datetime.now(UTC),
        )


class InMemorySummaryCache:
    def __init__(self) -> None:
        self._values: dict[str, AggregatedMetrics] = {}

    async def get(self, key: str) -> AggregatedMetrics | None:
        return self._values.get(key)

    async def set(
        self,
        key: str,
        value: AggregatedMetrics,
        *,
        ttl_seconds: int,
    ) -> None:
        del ttl_seconds
        self._values[key] = value


class InMemorySyncQueue:
    def __init__(self) -> None:
        self._jobs: dict[str, tuple[str, SyncJob]] = {}

    async def enqueue(self, job: SyncJob, *, idempotency_key: str) -> QueueResult:
        existing = self._jobs.get(idempotency_key)
        if existing is not None:
            return QueueResult(job_id=existing[0], duplicate=True)

        job_id = str(uuid4())
        self._jobs[idempotency_key] = (job_id, job)
        return QueueResult(job_id=job_id, duplicate=False)
