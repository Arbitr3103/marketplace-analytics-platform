from datetime import date

from fastapi.testclient import TestClient

from marketplace_analytics.config import Settings
from marketplace_analytics.infrastructure.memory import (
    InMemoryAnalyticsRepository,
    InMemorySummaryCache,
    InMemorySyncQueue,
)
from marketplace_analytics.main import create_app
from marketplace_analytics.service import AnalyticsService


def build_client() -> TestClient:
    service = AnalyticsService(
        repository=InMemoryAnalyticsRepository(),
        cache=InMemorySummaryCache(),
        queue=InMemorySyncQueue(),
        cache_ttl_seconds=60,
    )
    app = create_app(
        settings=Settings(environment="test", demo_mode=True),
        service=service,
    )
    return TestClient(app)


def test_health() -> None:
    with build_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "demo"}


def test_dashboard_contract() -> None:
    with build_client() as client:
        response = client.get("/api/v1/dashboard", params={"days": 30})

    assert response.status_code == 200
    payload = response.json()
    assert payload["period_days"] == 30
    assert payload["stores"] == 50
    assert payload["sku_count"] == 30_428
    assert payload["orders"] > 0
    assert payload["revenue"] > 0


def test_dashboard_query_validation() -> None:
    with build_client() as client:
        response = client.get("/api/v1/dashboard", params={"days": 0})

    assert response.status_code == 422


def test_sync_requires_idempotency_key() -> None:
    with build_client() as client:
        response = client.post(
            "/api/v1/sync",
            json={
                "provider": "demo",
                "date_from": date(2026, 7, 1).isoformat(),
                "date_to": date(2026, 7, 31).isoformat(),
            },
        )

    assert response.status_code == 422


def test_sync_duplicate_returns_same_job() -> None:
    headers = {"Idempotency-Key": "sync-july-2026"}
    body = {
        "provider": "demo",
        "date_from": "2026-07-01",
        "date_to": "2026-07-31",
    }

    with build_client() as client:
        first = client.post("/api/v1/sync", headers=headers, json=body)
        second = client.post("/api/v1/sync", headers=headers, json=body)

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["status"] == "queued"
    assert second.json()["status"] == "duplicate"
    assert first.json()["job_id"] == second.json()["job_id"]


def test_sync_period_limit() -> None:
    with build_client() as client:
        response = client.post(
            "/api/v1/sync",
            headers={"Idempotency-Key": "sync-too-long"},
            json={
                "provider": "demo",
                "date_from": "2026-01-01",
                "date_to": "2026-07-31",
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "sync period must not exceed 90 days"
