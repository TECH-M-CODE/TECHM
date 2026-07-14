import pytest
import json
from app.adapters.inject_adapter import InjectAdapter
from app.services.ingestion.ingestion_service import IngestionService
from app.infrastructure.broker import AsyncioMessageBroker
from app.infrastructure.uow import SQLAlchemyUnitOfWork
from typing import AsyncGenerator

@pytest.mark.asyncio
async def test_ingestion_deduplication(db_session):
    broker = AsyncioMessageBroker()
    adapter = InjectAdapter()
    
    # Inject two identical events
    event = {"name": "Test Target", "source": "News"}
    adapter.inject(event)
    adapter.inject(event)
    
    def uow_factory() -> AsyncGenerator[SQLAlchemyUnitOfWork, None]:
        async def _gen():
            yield SQLAlchemyUnitOfWork(db_session)
        return _gen()
        
    service = IngestionService(uow_factory=uow_factory, broker=broker, adapters=[adapter])
    
    # Process
    ingested_count = await service.poll_all()
    
    # Only 1 should be ingested because the second has the same hash
    assert ingested_count == 1
    
    uow = SQLAlchemyUnitOfWork(db_session)
    async with uow:
        raw_events = await uow.raw_events.get_unprocessed()
        assert len(raw_events) == 1
        
        # Check deduplication on a subsequent run
        adapter.inject(event)
        ingested_count_2 = await service.poll_all()
        assert ingested_count_2 == 0
