from typing import Any
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces import ISanctionsRepository
from app.domain.models.sanctions import SanctionsEntry

class SanctionsRepository(ISanctionsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_batch(
        self, entries: list[dict[str, Any]], source_list: str, version: int
    ) -> dict[str, int]:
        # Since this can be huge, we just use ORM for a simplified bulk insert in Phase 2.
        # In a real enterprise system we'd use sqlalchemy Core bulk inserts/upserts.
        
        # Deactivate previous active entries for this source_list
        deactivate_query = select(SanctionsEntry).where(
            SanctionsEntry.source_list == source_list,
            SanctionsEntry.is_active == True
        )
        old_result = await self.session.execute(deactivate_query)
        old_entries = old_result.scalars().all()
        for e in old_entries:
            e.is_active = False

        # Add new entries
        new_records = []
        for data in entries:
            entry = SanctionsEntry(
                original_id=data.get("original_id"),
                name=data.get("name", ""),
                aliases=data.get("aliases", []),
                country=data.get("country"),
                source_list=source_list,
                list_version=version,
                is_active=True
            )
            self.session.add(entry)
            new_records.append(entry)

        return {
            "inserted": len(new_records),
            "deactivated": len(old_entries)
        }

    async def get_active_names(self, source_list: str | None = None) -> list[tuple[str, str]]:
        query = select(SanctionsEntry.id, SanctionsEntry.name).where(SanctionsEntry.is_active == True)
        if source_list:
            query = query.where(SanctionsEntry.source_list == source_list)
        
        result = await self.session.execute(query)
        return [(str(row.id), row.name) for row in result.all()]

    async def search(self, name: str, limit: int = 10) -> list[SanctionsEntry]:
        query = select(SanctionsEntry).where(
            SanctionsEntry.is_active == True,
            SanctionsEntry.name.ilike(f"%{name}%")
        ).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_current_version(self, source_list: str) -> int:
        query = select(func.max(SanctionsEntry.list_version)).where(
            SanctionsEntry.source_list == source_list
        )
        result = await self.session.execute(query)
        val = result.scalar()
        return val if val is not None else 0
