from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces import ISARRepository
from app.domain.models.sar import SARDraft

class SARRepository(ISARRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict[str, Any]) -> SARDraft:
        sar = SARDraft(**data)
        self.session.add(sar)
        return sar

    async def get_by_id(self, sar_id: str) -> SARDraft | None:
        result = await self.session.execute(select(SARDraft).where(SARDraft.id == sar_id))
        return result.scalar_one_or_none()

    async def list_all(
        self, page: int = 1, page_size: int = 20, filters: dict[str, Any] | None = None
    ) -> tuple[list[SARDraft], int]:
        query = select(SARDraft)
        if filters:
            if "status" in filters:
                query = query.where(SARDraft.status == filters["status"])

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar_one()

        query = query.offset((page - 1) * page_size).limit(page_size).order_by(SARDraft.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all()), total_count

    async def update(self, sar_id: str, data: dict[str, Any]) -> SARDraft | None:
        sar = await self.get_by_id(sar_id)
        if not sar:
            return None
        for key, value in data.items():
            setattr(sar, key, value)
        return sar

    async def create_new_version(self, sar_id: str, data: dict[str, Any]) -> SARDraft | None:
        sar = await self.get_by_id(sar_id)
        if not sar:
            return None
        
        new_data = {
            "entity_id": sar.entity_id,
            "version": sar.version + 1,
            "status": data.get("status", sar.status),
            "narrative": data.get("narrative", sar.narrative)
        }
        
        # Depending on requirements, we might want to archive the old one instead of just 
        # creating a new version ID. The current model implies keeping both if they have different IDs.
        # But wait, `sar_id` is passed. If we want to create a new version of the SAME draft, 
        # usually it's a new row. We will return the new row.
        return await self.create(new_data)
