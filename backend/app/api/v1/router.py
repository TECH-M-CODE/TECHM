from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.entities import router as entities_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.sars import router as sars_router
from app.api.v1.audit import router as audit_router
from app.api.v1.events import router as events_router
from app.api.v1.demo import router as demo_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(entities_router)
router.include_router(alerts_router)
router.include_router(sars_router)
router.include_router(audit_router)
router.include_router(events_router)
router.include_router(demo_router)
