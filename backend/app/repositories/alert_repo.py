from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces import IAlertRepository
from app.domain.models.alert import Alert

class AlertRepository(IAlertRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict[str, Any]) -> Alert:
        alert = Alert(**data)
        self.session.add(alert)
        return alert

    async def get_by_id(self, alert_id: str) -> Alert | None:
        result = await self.session.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def list_all(
        self, page: int = 1, page_size: int = 20, filters: dict[str, Any] | None = None
    ) -> tuple[list[Alert], int]:
        query = select(Alert)
        if filters:
            if "status" in filters:
                query = query.where(Alert.status == filters["status"])
            if "priority" in filters:
                query = query.where(Alert.priority == filters["priority"])

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar_one()

        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Alert.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all()), total_count

    async def update(self, alert_id: str, data: dict[str, Any]) -> Alert | None:
        alert = await self.get_by_id(alert_id)
        if not alert:
            return None
        for key, value in data.items():
            setattr(alert, key, value)
        return alert
