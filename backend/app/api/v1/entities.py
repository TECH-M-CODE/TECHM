from fastapi import APIRouter, Depends, Request
from app.api.v1.router import APIResponse, PaginatedData
from app.domain.interfaces import IUnitOfWork
from app.dependencies import get_uow
from app.middleware.auth import get_current_user
import uuid

router = APIRouter(prefix="/entities", tags=["entities"])

@router.get("/", response_model=APIResponse[PaginatedData[dict]])
async def list_entities(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    risk_band: str = None,
    uow: IUnitOfWork = Depends(get_uow),
    _: dict = Depends(get_current_user)
):
    filters = {}
    if risk_band:
        filters["risk_band"] = risk_band
        
    async with uow:
        entities, total = await uow.entities.list_all(page, page_size, filters)
        
    data = PaginatedData(
        items=[{"id": str(e.id), "name": e.name, "risk_score": e.risk_score, "risk_band": e.risk_band} for e in entities],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
    return APIResponse(success=True, message="Entities retrieved", data=data, trace_id=request.state.trace_id)

@router.get("/{entity_id}", response_model=APIResponse[dict])
async def get_entity(
    request: Request,
    entity_id: str,
    uow: IUnitOfWork = Depends(get_uow),
    _: dict = Depends(get_current_user)
):
    async with uow:
        entity = await uow.entities.get_by_id(entity_id)
        
    if not entity:
        return APIResponse(success=False, message="Entity not found", data=None, trace_id=request.state.trace_id)
        
    data = {"id": str(entity.id), "name": entity.name, "risk_score": entity.risk_score, "risk_band": entity.risk_band, "country": entity.country}
    return APIResponse(success=True, message="Entity retrieved", data=data, trace_id=request.state.trace_id)
