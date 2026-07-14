from fastapi import APIRouter, Depends, Request
from app.api.v1.router import APIResponse, PaginatedData
from app.domain.interfaces import IUnitOfWork
from app.dependencies import get_uow
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=APIResponse[PaginatedData[dict]])
async def list_alerts(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    uow: IUnitOfWork = Depends(get_uow),
    _: dict = Depends(get_current_user)
):
    filters = {}
    if status:
        filters["status"] = status
        
    async with uow:
        alerts, total = await uow.alerts.list_all(page, page_size, filters)
        
    data = PaginatedData(
        items=[{"id": str(a.id), "entity_id": str(a.entity_id), "alert_type": a.alert_type, "status": a.status, "priority": a.priority} for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
    return APIResponse(success=True, message="Alerts retrieved", data=data, trace_id=request.state.trace_id)
