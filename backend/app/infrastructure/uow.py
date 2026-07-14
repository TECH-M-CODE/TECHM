from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces import IUnitOfWork
from app.repositories import (
    EntityRepository,
    RawEventRepository,
    RiskEventRepository,
    AlertRepository,
    SARRepository,
    AuditRepository,
    SanctionsRepository,
)

class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        # Initialize repositories with the shared session
        self.entities = EntityRepository(self._session)
        self.raw_events = RawEventRepository(self._session)
        self.risk_events = RiskEventRepository(self._session)
        self.alerts = AlertRepository(self._session)
        self.sars = SARRepository(self._session)
        self.audit = AuditRepository(self._session)
        self.sanctions = SanctionsRepository(self._session)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            # We don't automatically commit here, standard UoW practice is to require 
            # an explicit commit call in the service layer, otherwise we rollback.
            # But in some patterns, exiting without error commits. 
            # We will require explicit commit to prevent accidental partial commits.
            await self.rollback()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
