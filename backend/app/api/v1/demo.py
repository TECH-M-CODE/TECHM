from fastapi import APIRouter, Depends, Request
from app.api.v1.router import APIResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/demo", tags=["demo"])

@router.get("/scenarios", response_model=APIResponse[list[dict]])
async def list_scenarios(
    request: Request,
    _: dict = Depends(get_current_user)
):
    scenarios = [
        {"id": "money_laundering", "name": "Money Laundering", "description": "Simulates a complex money laundering trace."},
        {"id": "sanction_case", "name": "Sanction Evasion", "description": "Simulates a sanction evasion via shell company."},
        {"id": "fake_news", "name": "Fake News Challenge", "description": "Tests the verification engine against a false media report."}
    ]
    return APIResponse(success=True, message="Scenarios retrieved", data=scenarios, trace_id=getattr(request.state, "trace_id", "local-trace"))

@router.post("/scenarios/{scenario_id}/trigger", response_model=APIResponse[dict])
async def trigger_scenario(
    request: Request,
    scenario_id: str,
    _: dict = Depends(get_current_user)
):
    # Mock response
    return APIResponse(success=True, message=f"Scenario {scenario_id} triggered", data={"status": "running", "scenario_id": scenario_id}, trace_id=getattr(request.state, "trace_id", "local-trace"))
