"""FastAPI routes."""

from typing import Annotated, cast

from fastapi import APIRouter, Header, HTTPException, Query, Request, status

from marketplace_analytics.contracts import (
    DashboardSummary,
    SyncAccepted,
    SyncRequest,
)
from marketplace_analytics.service import AnalyticsService

router = APIRouter(prefix="/api/v1")


def service_from_request(request: Request) -> AnalyticsService:
    return cast(AnalyticsService, request.app.state.analytics_service)


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard(
    request: Request,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> DashboardSummary:
    service = service_from_request(request)
    try:
        return await service.dashboard(days=days)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post("/sync", response_model=SyncAccepted, status_code=status.HTTP_202_ACCEPTED)
async def request_sync(
    payload: SyncRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> SyncAccepted:
    service = service_from_request(request)
    try:
        return await service.request_sync(payload, idempotency_key=idempotency_key)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
