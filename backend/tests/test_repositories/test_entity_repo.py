import pytest
from app.infrastructure.uow import SQLAlchemyUnitOfWork

@pytest.mark.asyncio
async def test_entity_repo_crud(db_session):
    uow = SQLAlchemyUnitOfWork(db_session)
    
    async with uow:
        # Create
        entity = await uow.entities.create({
            "name": "Acme Corp",
            "country": "USA",
            "risk_score": 0.0,
            "risk_band": "low"
        })
        await uow.commit()
        
        # Read
        fetched = await uow.entities.get_by_id(str(entity.id))
        assert fetched is not None
        assert fetched.name == "Acme Corp"
        
        # Update
        updated = await uow.entities.update(str(entity.id), {"risk_score": 85.0})
        assert updated.risk_score == 85.0
        
        # Update specific risk method
        await uow.entities.update_risk_score(str(entity.id), 90.0, "high")
        await uow.commit()
        
    async with uow:
        # Verify update persisted
        fetched = await uow.entities.get_by_id(str(entity.id))
        assert fetched.risk_score == 90.0
        assert fetched.risk_band == "high"

        # List
        items, count = await uow.entities.list_all(filters={"risk_band": "high"})
        assert count == 1
        assert len(items) == 1
        assert items[0].name == "Acme Corp"
