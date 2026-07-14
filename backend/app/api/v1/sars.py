from fastapi import APIRouter, Depends, Request
from app.api.v1.router import APIResponse, PaginatedData
from app.domain.interfaces import IUnitOfWork
from app.dependencies import get_uow
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/sars", tags=["sars"])

@router.get("/", response_model=APIResponse[PaginatedData[dict]])
async def list_sars(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    uow: IUnitOfWork = Depends(get_uow),
    _: dict = Depends(get_current_user)
):
    async with uow:
        sars, total = await uow.sars.list_all(page, page_size)
        
    data = PaginatedData(
        items=[{"id": str(s.id), "entity_id": str(s.entity_id), "status": s.status, "version": s.version} for s in sars],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
    return APIResponse(success=True, message="SARs retrieved", data=data, trace_id=request.state.trace_id)
