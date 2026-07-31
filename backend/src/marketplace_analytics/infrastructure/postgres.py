"""Async SQLAlchemy repository for aggregated daily metrics."""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import Date, DateTime, Float, Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from marketplace_analytics.domain import AggregatedMetrics


class Base(DeclarativeBase):
    pass


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_date: Mapped[date] = mapped_column(Date, index=True)
    store_id: Mapped[str] = mapped_column(index=True)
    sku_count: Mapped[int] = mapped_column(Integer)
    orders: Mapped[int] = mapped_column(Integer)
    revenue: Mapped[float] = mapped_column(Float)
    stock_alerts: Mapped[int] = mapped_column(Integer)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class PostgresAnalyticsRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def aggregate(self, *, days: int) -> AggregatedMetrics:
        cutoff = date.today() - timedelta(days=days - 1)
        statement = select(
            func.count(func.distinct(DailyMetric.store_id)),
            func.max(DailyMetric.sku_count),
            func.sum(DailyMetric.orders),
            func.sum(DailyMetric.revenue),
            func.max(DailyMetric.stock_alerts),
            func.max(DailyMetric.collected_at),
        ).where(DailyMetric.metric_date >= cutoff)

        async with self._session_factory() as session:
            row = (await session.execute(statement)).one()

        return AggregatedMetrics(
            stores=int(row[0] or 0),
            sku_count=int(row[1] or 0),
            orders=int(row[2] or 0),
            revenue=float(row[3] or 0.0),
            stock_alerts=int(row[4] or 0),
            generated_at=row[5] or datetime.now(UTC),
        )
