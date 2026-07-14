from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces import IRawEventRepository
from app.domain.models.event import RawEvent

class RawEventRepository(IRawEventRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict[str, Any]) -> RawEvent:
        event = RawEvent(**data)
        self.session.add(event)
        return event

    async def exists_by_hash(self, content_hash: str) -> bool:
        query = select(RawEvent.id).where(RawEvent.content_hash == content_hash)
        result = await self.session.execute(query)
        return result.first() is not None

    async def get_unprocessed(self, limit: int = 50) -> list[RawEvent]:
        query = select(RawEvent).where(RawEvent.processing_status == "pending").limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(self, event_id: str, status: str) -> None:
        query = select(RawEvent).where(RawEvent.id == event_id)
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        if event:
            event.processing_status = status
