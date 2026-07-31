"""Redis cache and idempotent queue adapters.

The redis dependency is imported lazily so local demo tests do not require a Redis client.
"""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from marketplace_analytics.domain import AggregatedMetrics, QueueResult, SyncJob


class RedisSummaryCache:
    def __init__(self, client: Any) -> None:
        self._client = client

    @classmethod
    def from_url(cls, url: str) -> "RedisSummaryCache":
        from redis.asyncio import Redis

        return cls(Redis.from_url(url, decode_responses=True))

    async def get(self, key: str) -> AggregatedMetrics | None:
        payload = await self._client.get(key)
        if payload is None:
            return None
        data = json.loads(payload)
        return AggregatedMetrics(
            stores=int(data["stores"]),
            sku_count=int(data["sku_count"]),
            orders=int(data["orders"]),
            revenue=float(data["revenue"]),
            stock_alerts=int(data["stock_alerts"]),
            generated_at=datetime.fromisoformat(data["generated_at"]),
        )

    async def set(
        self,
        key: str,
        value: AggregatedMetrics,
        *,
        ttl_seconds: int,
    ) -> None:
        data = asdict(value)
        data["generated_at"] = value.generated_at.isoformat()
        await self._client.set(key, json.dumps(data), ex=ttl_seconds)

    async def close(self) -> None:
        await self._client.aclose()


class RedisSyncQueue:
    def __init__(self, client: Any, *, queue_name: str = "marketplace:sync") -> None:
        self._client = client
        self._queue_name = queue_name

    @classmethod
    def from_url(cls, url: str) -> "RedisSyncQueue":
        from redis.asyncio import Redis

        return cls(Redis.from_url(url, decode_responses=True))

    async def enqueue(self, job: SyncJob, *, idempotency_key: str) -> QueueResult:
        job_id = str(uuid4())
        dedupe_key = f"marketplace:sync:idempotency:{idempotency_key}"
        accepted = await self._client.set(dedupe_key, job_id, nx=True, ex=86_400)
        if not accepted:
            existing_id = await self._client.get(dedupe_key)
            return QueueResult(job_id=str(existing_id), duplicate=True)

        payload = {
            "job_id": job_id,
            "provider": job.provider,
            "date_from": job.date_from.isoformat(),
            "date_to": job.date_to.isoformat(),
            "requested_at": job.requested_at.isoformat(),
        }
        try:
            await self._client.rpush(self._queue_name, json.dumps(payload))
        except Exception:
            await self._client.delete(dedupe_key)
            raise
        return QueueResult(job_id=job_id, duplicate=False)

    async def close(self) -> None:
        await self._client.aclose()
