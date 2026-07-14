from fastapi import APIRouter, Depends, Request
from app.api.v1.router import APIResponse
from app.domain.interfaces import IUnitOfWork
from app.dependencies import get_uow, get_secrets
from app.middleware.auth import get_current_user
from app.services.audit.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/verify", response_model=APIResponse[dict])
async def verify_audit_chain(
    request: Request,
    uow_gen = Depends(get_uow),
    secrets = Depends(get_secrets),
    _: dict = Depends(get_current_user)
):
    # Pass a factory lambda that returns the dependency generator
    audit_service = AuditService(uow_factory=lambda: uow_gen, secrets_manager=secrets)
    valid, message = await audit_service.verify_chain()
    
    return APIResponse(
        success=valid, 
        message=message, 
        data={"valid": valid}, 
        trace_id=request.state.trace_id
    )
