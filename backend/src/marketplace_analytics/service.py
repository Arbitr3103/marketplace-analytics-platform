"""Application service for dashboards and idempotent sync requests."""

from datetime import UTC, datetime

from marketplace_analytics.contracts import DashboardSummary, SyncAccepted, SyncRequest
from marketplace_analytics.domain import AnalyticsRepository, SummaryCache, SyncJob, SyncQueue


class AnalyticsService:
    def __init__(
        self,
        *,
        repository: AnalyticsRepository,
        cache: SummaryCache,
        queue: SyncQueue,
        cache_ttl_seconds: int,
    ) -> None:
        self._repository = repository
        self._cache = cache
        self._queue = queue
        self._cache_ttl_seconds = cache_ttl_seconds

    async def dashboard(self, *, days: int) -> DashboardSummary:
        if not 1 <= days <= 365:
            raise ValueError("days must be between 1 and 365")

        cache_key = f"dashboard:{days}"
        metrics = await self._cache.get(cache_key)
        if metrics is None:
            metrics = await self._repository.aggregate(days=days)
            await self._cache.set(
                cache_key,
                metrics,
                ttl_seconds=self._cache_ttl_seconds,
            )

        average_order_value = metrics.revenue / metrics.orders if metrics.orders else 0.0
        return DashboardSummary(
            period_days=days,
            stores=metrics.stores,
            sku_count=metrics.sku_count,
            orders=metrics.orders,
            revenue=round(metrics.revenue, 2),
            average_order_value=round(average_order_value, 2),
            stock_alerts=metrics.stock_alerts,
            generated_at=metrics.generated_at,
        )

    async def request_sync(
        self,
        request: SyncRequest,
        *,
        idempotency_key: str,
    ) -> SyncAccepted:
        request.validate_period()
        normalized_key = idempotency_key.strip()
        if not 8 <= len(normalized_key) <= 128:
            raise ValueError("Idempotency-Key must contain 8-128 characters")

        result = await self._queue.enqueue(
            SyncJob(
                provider=request.provider,
                date_from=request.date_from,
                date_to=request.date_to,
                requested_at=datetime.now(UTC),
            ),
            idempotency_key=normalized_key,
        )
        return SyncAccepted(
            job_id=result.job_id,
            status="duplicate" if result.duplicate else "queued",
            idempotency_key=normalized_key,
        )
