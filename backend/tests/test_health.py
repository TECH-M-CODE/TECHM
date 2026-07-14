import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_returns_200(test_client: AsyncClient):
    """Test that the health endpoint returns 200 OK and success=True."""
    response = await test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_health_contains_status(test_client: AsyncClient):
    """Test that the health endpoint contains the required status fields."""
    response = await test_client.get("/api/v1/health")
    data = response.json()["data"]
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data
    assert data["db_connected"] is True
    assert data["version"] == "1.0.0"

@pytest.mark.asyncio
async def test_db_tables_created(db_engine):
    """Test that all tables are created by inspecting the metadata."""
    from app.domain.models.base import Base
    
    async with db_engine.begin() as conn:
        # Use SQLAlchemy inspect to check tables
        def get_table_names(connection):
            from sqlalchemy import inspect
            return inspect(connection).get_table_names()
            
        tables = await conn.run_sync(get_table_names)
        
        # Verify our main tables exist
        expected_tables = [
            "entities", "entity_persons", "events_raw", 
            "risk_events", "alerts", "sar_drafts", 
            "audit_log", "sanctions_cache", "users"
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} was not created"
