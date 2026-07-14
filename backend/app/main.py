from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

from app.config import Settings, get_settings
from app.infrastructure.database import init_db, close_db
from app.infrastructure.vector_store import init_vector_store

logger = logging.getLogger(__name__)

# Track startup time for uptime calculation
START_TIME = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    settings = get_settings()
    logger.info(f"Starting SentinelAI in {settings.environment} environment")
    
    # Initialize database
    await init_db()
    
    # Initialize Vector Store (ChromaDB)
    await init_vector_store(settings.chroma_persist_dir)
    
    yield
    
    # Cleanup on shutdown
    await close_db()
    logger.info("SentinelAI shutdown complete")

app = FastAPI(
    title="SentinelAI API",
    description="Autonomous Continuous KYC Compliance Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check endpoint to verify system is operational."""
    uptime = time.time() - START_TIME
    return {
        "success": True, 
        "message": "System is healthy",
        "data": {
            "status": "healthy",
            "environment": settings.environment,
            "uptime_seconds": round(uptime, 2),
            "db_connected": True,
            "version": "1.0.0"
        }
    }
