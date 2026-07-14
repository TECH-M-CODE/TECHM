import pytest
import json
from app.services.screening.screening_service import ScreeningService
from app.infrastructure.cache import InMemoryCacheProvider
from app.infrastructure.uow import SQLAlchemyUnitOfWork
from typing import AsyncGenerator

@pytest.mark.asyncio
async def test_fuzzy_matching(db_session):
    def uow_factory() -> AsyncGenerator[SQLAlchemyUnitOfWork, None]:
        async def _gen():
            yield SQLAlchemyUnitOfWork(db_session)
        return _gen()
        
    # Setup UoW and seed some data
    uow = SQLAlchemyUnitOfWork(db_session)
    async with uow:
        # Create a known entity
        await uow.entities.create({
            "name": "Osama Bin Laden",
            "country": "Unknown",
            "risk_score": 100.0,
            "risk_band": "critical"
        })
        
        # Create a raw event with a slight misspelling
        await uow.raw_events.create({
            "content_hash": "hash123",
            "content": json.dumps({"name": "Usama Bin Ladin", "type": "transfer"}),
            "processing_status": "pending"
        })
        await uow.commit()

    cache = InMemoryCacheProvider()
    service = ScreeningService(uow_factory=uow_factory, cache=cache)
    
    # Override match threshold just for testing if needed, default 85 is fine
    screened_payloads = await service.screen_pending_events()
    
    assert len(screened_payloads) == 1
    matches = screened_payloads[0]["screening_matches"]
    
    # Should have matched "Osama Bin Laden" despite spelling difference
    assert len(matches) > 0
    assert matches[0]["name"] == "Osama Bin Laden"
    assert matches[0]["score"] > 80.0
    
    # Check that raw event is no longer pending
    async with uow:
        raw_events = await uow.raw_events.get_unprocessed()
        assert len(raw_events) == 0
