import json
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces import IEntityRepository
from app.domain.models.entity import Entity

class EntityRepository(IEntityRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict[str, Any]) -> Entity:
        entity = Entity(**data)
        self.session.add(entity)
        return entity

    async def get_by_id(self, entity_id: str) -> Entity | None:
        result = await self.session.execute(select(Entity).where(Entity.id == entity_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Entity | None:
        result = await self.session.execute(select(Entity).where(Entity.name == name))
        return result.scalar_one_or_none()

    async def list_all(
        self, page: int = 1, page_size: int = 20, filters: dict[str, Any] | None = None
    ) -> tuple[list[Entity], int]:
        query = select(Entity)
        if filters:
            if "risk_band" in filters:
                query = query.where(Entity.risk_band == filters["risk_band"])
            if "country" in filters:
                query = query.where(Entity.country == filters["country"])
                
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar_one()

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total_count

    async def update(self, entity_id: str, data: dict[str, Any]) -> Entity | None:
        entity = await self.get_by_id(entity_id)
        if not entity:
            return None
        for key, value in data.items():
            setattr(entity, key, value)
        return entity

    async def update_risk_score(self, entity_id: str, new_score: float, new_band: str) -> Entity | None:
        entity = await self.get_by_id(entity_id)
        if not entity:
            return None
        entity.risk_score = new_score
        entity.risk_band = new_band
        return entity

    async def search(self, query_str: str, limit: int = 20) -> list[Entity]:
        # Using basic ILIKE for SQLite. For postgres this would use pg_trgm.
        query = select(Entity).where(Entity.name.ilike(f"%{query_str}%")).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_names(self) -> list[tuple[str, str]]:
        query = select(Entity.id, Entity.name)
        result = await self.session.execute(query)
        return [(str(row.id), row.name) for row in result.all()]
