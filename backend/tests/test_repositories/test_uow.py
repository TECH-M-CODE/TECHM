import pytest
from app.infrastructure.uow import SQLAlchemyUnitOfWork

@pytest.mark.asyncio
async def test_uow_commit_and_rollback(db_session):
    uow = SQLAlchemyUnitOfWork(db_session)
    
    async with uow:
        # Create an entity
        entity = await uow.entities.create({
            "name": "Test UoW Entity",
            "risk_score": 10.0,
            "risk_band": "low"
        })
        # Note: We do NOT commit here yet
        
    # Standard UoW pattern: exit WITHOUT explicit commit means rollback
    # So the entity should not exist
    result = await uow.entities.get_by_name("Test UoW Entity")
    assert result is None

    async with uow:
        entity = await uow.entities.create({
            "name": "Test UoW Entity 2",
            "risk_score": 10.0,
            "risk_band": "low"
        })
        await uow.commit()
        
    result = await uow.entities.get_by_name("Test UoW Entity 2")
    assert result is not None
    assert result.name == "Test UoW Entity 2"

@pytest.mark.asyncio
async def test_uow_rollback_on_exception(db_session):
    uow = SQLAlchemyUnitOfWork(db_session)
    
    try:
        async with uow:
            await uow.entities.create({
                "name": "Should Rollback",
                "risk_score": 50.0,
                "risk_band": "high"
            })
            raise ValueError("Something went wrong!")
    except ValueError:
        pass
        
    # Transaction should have rolled back
    result = await uow.entities.get_by_name("Should Rollback")
    assert result is None
