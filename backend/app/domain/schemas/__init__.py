"""Pydantic schemas — request/response DTOs.

Every API returns: { success: bool, message: str, data: T }
Every AI agent returns structured JSON, never plain text.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Standard API Response Envelope ──────────────────────────


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper. Every endpoint returns this shape."""
    success: bool = True
    message: str = ""
    data: T | None = None


class PaginatedData(BaseModel, Generic[T]):
    """Paginated response data."""
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


# ── Entity Schemas ──────────────────────────────────────────


class EntityCreate(BaseModel):
    """Request body for creating a monitored entity."""
    name: str = Field(..., min_length=1, max_length=500)
    entity_type: str = Field(..., pattern="^(corporate|individual|financial_institution)$")
    country: str = Field(default="", max_length=5)
    sector: str = Field(default="", max_length=100)
    sector_risk: str = Field(default="low", pattern="^(low|medium|high)$")
    pep_flag: bool = False
    sanctions_flag: bool = False
    fatf_country_flag: bool = False
    aliases: str = Field(default="")
    description: str = Field(default="")
    external_id: str | None = None


class EntityUpdate(BaseModel):
    """Request body for updating an entity."""
    name: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, pattern="^(active|inactive|under_review|deregistered)$")
    country: str | None = Field(default=None, max_length=5)
    sector: str | None = Field(default=None, max_length=100)
    pep_flag: bool | None = None
    sanctions_flag: bool | None = None
    aliases: str | None = None
    description: str | None = None


class EntityResponse(BaseModel):
    """Entity data returned to the client."""
    id: str
    name: str
    entity_type: str
    status: str
    country: str
    sector: str
    sector_risk: str
    pep_flag: bool
    sanctions_flag: bool
    fatf_country_flag: bool
    risk_score: float
    risk_band: str
    aliases: str
    description: str
    external_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Alert Schemas ───────────────────────────────────────────


class AlertResponse(BaseModel):
    """Alert data returned to the client."""
    id: str
    entity_id: str
    risk_event_id: str
    alert_type: str
    priority: str
    status: str
    title: str
    summary: str
    evidence_bundle: str
    ai_reasoning: str
    ai_confidence: str
    assigned_to: str | None
    reviewed_by: str | None
    review_notes: str
    disposition: str | None
    is_drill: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertAction(BaseModel):
    """Request body for acting on an alert."""
    action: str = Field(..., pattern="^(dismiss|escalate|review|assign)$")
    notes: str = Field(default="")
    assigned_to: str | None = None


# ── SAR Schemas ─────────────────────────────────────────────


class SARResponse(BaseModel):
    """SAR draft data returned to the client."""
    id: str
    entity_id: str
    alert_id: str
    status: str
    version: int
    narrative: str
    regulatory_basis: str
    evidence_citations: str
    risk_summary: str
    entity_name: str
    entity_risk_score: str
    entity_risk_band: str
    reviewed_by: str | None
    review_notes: str
    decision: str | None
    previous_version_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SARDecision(BaseModel):
    """Request body for SAR review decision."""
    decision: str = Field(..., pattern="^(approve|reject|request_more_info)$")
    notes: str = Field(default="")


class SAREdit(BaseModel):
    """Request body for editing a SAR draft narrative."""
    narrative: str = Field(..., min_length=1)


# ── Risk Event Schemas ──────────────────────────────────────


class RiskEventResponse(BaseModel):
    """Risk event data returned to the client."""
    id: str
    entity_id: str
    raw_event_id: str
    event_type: str
    severity: str
    score_delta: float
    score_after: float
    band_after: str
    evidence_summary: str
    ai_reasoning: str
    ai_confidence: float
    country_code: str
    source: str
    is_indirect: bool
    source_entity_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Audit Schemas ───────────────────────────────────────────


class AuditEntryResponse(BaseModel):
    """Audit log entry returned to the client."""
    id: str
    action: str
    actor_type: str
    actor_id: str
    entity_id: str | None
    alert_id: str | None
    sar_id: str | None
    event_id: str | None
    details: str
    reasoning: str
    entry_hash: str
    previous_hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditChainVerification(BaseModel):
    """Result of verifying the audit hash chain."""
    is_valid: bool
    total_entries: int
    verified_entries: int
    first_broken_entry_id: str | None = None
    message: str = ""


# ── Auth Schemas ────────────────────────────────────────────


class UserCreate(BaseModel):
    """Request body for user registration."""
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="viewer", pattern="^(compliance_officer|administrator|auditor|viewer)$")


class UserLogin(BaseModel):
    """Request body for login."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UserResponse(BaseModel):
    """User data returned to the client (no password)."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Agent Output Schemas ────────────────────────────────────
# Every agent returns structured JSON with reasoning, confidence,
# evidence, and citations. Never plain text.


class AgentOutput(BaseModel):
    """Base structure for all agent outputs."""
    agent_name: str
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = []
    citations: list[str] = []
    metadata: dict[str, Any] = {}


class EvidenceItem(BaseModel):
    """A single piece of evidence gathered by an agent."""
    source: str
    snippet: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    url: str = ""
    timestamp: str = ""


class EntityResolutionResult(BaseModel):
    """Output from the Entity Resolution Agent."""
    is_match: bool
    entity_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    alternative_matches: list[dict[str, Any]] = []


class EventClassification(BaseModel):
    """Output from event type/severity classification."""
    event_type: str
    severity: str
    reasoning: str = ""
    confidence: float = Field(ge=0.0, le=1.0)


# Fix forward reference
AgentOutput.model_rebuild()
