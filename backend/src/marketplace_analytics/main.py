"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from marketplace_analytics.api import router
from marketplace_analytics.config import Settings, get_settings
from marketplace_analytics.infrastructure.memory import (
    InMemoryAnalyticsRepository,
    InMemorySummaryCache,
    InMemorySyncQueue,
)
from marketplace_analytics.infrastructure.postgres import PostgresAnalyticsRepository
from marketplace_analytics.infrastructure.redis import RedisSummaryCache, RedisSyncQueue
from marketplace_analytics.service import AnalyticsService


def create_app(
    *,
    settings: Settings | None = None,
    service: AnalyticsService | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    engine: AsyncEngine | None = None
    redis_cache: RedisSummaryCache | None = None
    redis_queue: RedisSyncQueue | None = None

    if service is None and resolved_settings.demo_mode:
        service = AnalyticsService(
            repository=InMemoryAnalyticsRepository(),
            cache=InMemorySummaryCache(),
            queue=InMemorySyncQueue(),
            cache_ttl_seconds=resolved_settings.cache_ttl_seconds,
        )
    elif service is None:
        engine = create_async_engine(
            resolved_settings.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        redis_cache = RedisSummaryCache.from_url(resolved_settings.redis_url)
        redis_queue = RedisSyncQueue.from_url(resolved_settings.redis_url)
        service = AnalyticsService(
            repository=PostgresAnalyticsRepository(session_factory),
            cache=redis_cache,
            queue=redis_queue,
            cache_ttl_seconds=resolved_settings.cache_ttl_seconds,
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if redis_cache is not None:
                await redis_cache.close()
            if redis_queue is not None:
                await redis_queue.close()
            if engine is not None:
                await engine.dispose()

    app = FastAPI(
        title="Marketplace Analytics Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.analytics_service = service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )
    app.include_router(router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "mode": "demo" if resolved_settings.demo_mode else "services"}

    return app


app = create_app()
