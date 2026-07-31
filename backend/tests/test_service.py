from datetime import date

import pytest

from marketplace_analytics.contracts import SyncRequest
from marketplace_analytics.infrastructure.memory import (
    InMemoryAnalyticsRepository,
    InMemorySummaryCache,
    InMemorySyncQueue,
)
from marketplace_analytics.service import AnalyticsService


def build_service() -> tuple[AnalyticsService, InMemoryAnalyticsRepository]:
    repository = InMemoryAnalyticsRepository()
    service = AnalyticsService(
        repository=repository,
        cache=InMemorySummaryCache(),
        queue=InMemorySyncQueue(),
        cache_ttl_seconds=60,
    )
    return service, repository


@pytest.mark.asyncio
async def test_dashboard_uses_cache_for_same_period() -> None:
    service, repository = build_service()

    first = await service.dashboard(days=30)
    second = await service.dashboard(days=30)

    assert first == second
    assert first.stores == 50
    assert first.sku_count == 30_428
    assert repository.aggregate_calls == 1


@pytest.mark.asyncio
async def test_dashboard_rejects_out_of_range_period() -> None:
    service, _ = build_service()

    with pytest.raises(ValueError, match="between 1 and 365"):
        await service.dashboard(days=0)


@pytest.mark.asyncio
async def test_sync_is_idempotent() -> None:
    service, _ = build_service()
    request = SyncRequest(
        provider="demo",
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
    )

    first = await service.request_sync(request, idempotency_key="sync-july-2026")
    second = await service.request_sync(request, idempotency_key="sync-july-2026")

    assert first.status == "queued"
    assert second.status == "duplicate"
    assert second.job_id == first.job_id


@pytest.mark.asyncio
async def test_sync_rejects_reversed_period() -> None:
    service, _ = build_service()
    request = SyncRequest(
        provider="demo",
        date_from=date(2026, 7, 31),
        date_to=date(2026, 7, 1),
    )

    with pytest.raises(ValueError, match="date_from"):
        await service.request_sync(request, idempotency_key="sync-july-2026")
