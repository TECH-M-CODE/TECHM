from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces import IAuditRepository
from app.domain.models.audit import AuditEntry

class AuditRepository(IAuditRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append(self, data: dict[str, Any]) -> AuditEntry:
        # Append-only. No updates/deletes permitted.
        entry = AuditEntry(**data)
        self.session.add(entry)
        return entry

    async def get_by_entity(self, entity_id: str, limit: int = 100) -> list[AuditEntry]:
        query = select(AuditEntry).where(
            AuditEntry.entity_id == entity_id
        ).order_by(AuditEntry.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_chain(self, limit: int = 1000) -> list[AuditEntry]:
        # Return the global chain ordered chronologically for verification
        query = select(AuditEntry).order_by(AuditEntry.created_at.asc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest(self) -> AuditEntry | None:
        query = select(AuditEntry).order_by(AuditEntry.created_at.desc()).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(
        self, page: int = 1, page_size: int = 20, filters: dict[str, Any] | None = None
    ) -> tuple[list[AuditEntry], int]:
        query = select(AuditEntry)
        if filters:
            if "entity_id" in filters:
                query = query.where(AuditEntry.entity_id == filters["entity_id"])
            if "action" in filters:
                query = query.where(AuditEntry.action == filters["action"])

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar_one()

        query = query.offset((page - 1) * page_size).limit(page_size).order_by(AuditEntry.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all()), total_count
