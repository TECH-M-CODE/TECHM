import datetime
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces import IRiskEventRepository
from app.domain.models.event import RiskEvent

class RiskEventRepository(IRiskEventRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict[str, Any]) -> RiskEvent:
        event = RiskEvent(**data)
        self.session.add(event)
        return event

    async def get_by_entity(self, entity_id: str, limit: int = 50) -> list[RiskEvent]:
        query = select(RiskEvent).where(
            RiskEvent.entity_id == entity_id
        ).order_by(RiskEvent.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_score_deltas(self, entity_id: str, days: int = 7) -> list[float]:
        cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
        query = select(RiskEvent.score_delta).where(
            RiskEvent.entity_id == entity_id,
            RiskEvent.created_at >= cutoff
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
