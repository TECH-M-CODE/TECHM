"""Domain enumerations for SentinelAI.

All enums used across models, schemas, and business logic are defined here
to maintain a single source of truth.
"""

from __future__ import annotations

import enum


class EntityType(str, enum.Enum):
    """Type of monitored entity."""
    CORPORATE = "corporate"
    INDIVIDUAL = "individual"
    FINANCIAL_INSTITUTION = "financial_institution"


class EntityStatus(str, enum.Enum):
    """Lifecycle status of a monitored entity."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"
    DEREGISTERED = "deregistered"


class RiskBand(str, enum.Enum):
    """Risk classification band. Thresholds defined in risk_policy.yaml."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(str, enum.Enum):
    """Classification of risk-signal events."""
    SANCTIONS_HIT = "sanctions_hit"
    ADVERSE_MEDIA = "adverse_media"
    PEP_ASSOCIATION = "pep_association"
    REGULATORY_ACTION = "regulatory_action"
    TRANSACTION_ANOMALY = "transaction_anomaly"
    OWNERSHIP_CHANGE = "ownership_change"
    JURISDICTION_CHANGE = "jurisdiction_change"
    DORMANCY_SIGNAL = "dormancy_signal"
    SANCTIONS_LIST_ADDITION = "sanctions_list_addition"
    DRILL_EVENT = "drill_event"


class EventSource(str, enum.Enum):
    """Origin of a raw event."""
    GDELT = "gdelt"
    GNEWS = "gnews"
    RSS = "rss"
    OPENSANCTIONS = "opensanctions"
    OFAC = "ofac"
    TRANSACTION_MONITOR = "transaction_monitor"
    INJECT = "inject"
    PROVIDED_DATASET = "provided_dataset"
    MANUAL = "manual"


class Severity(str, enum.Enum):
    """Event severity classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class AlertStatus(str, enum.Enum):
    """Lifecycle status of an alert."""
    NEW = "new"
    UNDER_REVIEW = "under_review"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"


class AlertPriority(str, enum.Enum):
    """Alert priority derived from risk band and velocity."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SARStatus(str, enum.Enum):
    """SAR draft lifecycle. No SAR is ever auto-filed."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    REVISION_REQUESTED = "revision_requested"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuditAction(str, enum.Enum):
    """Every auditable action in the system."""
    # Event pipeline
    EVENT_INGESTED = "event_ingested"
    EVENT_DEDUPLICATED = "event_deduplicated"
    EVENT_SCREENED_OUT = "event_screened_out"
    EVENT_SCREENED_IN = "event_screened_in"

    # Entity resolution
    ENTITY_RESOLVED = "entity_resolved"
    ENTITY_RESOLUTION_DISMISSED = "entity_resolution_dismissed"
    ENTITY_RESOLUTION_QUEUED = "entity_resolution_queued"

    # Risk scoring
    RISK_SCORED = "risk_scored"
    RISK_BAND_CHANGED = "risk_band_changed"
    INDIRECT_EXPOSURE_PROPAGATED = "indirect_exposure_propagated"

    # Alerts
    ALERT_CREATED = "alert_created"
    ALERT_REVIEWED = "alert_reviewed"
    ALERT_ESCALATED = "alert_escalated"
    ALERT_DISMISSED = "alert_dismissed"

    # SAR
    SAR_DRAFT_CREATED = "sar_draft_created"
    SAR_EDITED = "sar_edited"
    SAR_APPROVED = "sar_approved"
    SAR_REJECTED = "sar_rejected"
    SAR_MORE_INFO_REQUESTED = "sar_more_info_requested"

    # Sanctions
    SANCTIONS_LIST_REFRESHED = "sanctions_list_refreshed"

    # System
    POLICY_RELOADED = "policy_reloaded"
    DRILL_EXECUTED = "drill_executed"
    DORMANCY_FLAGGED = "dormancy_flagged"

    # Human actions
    HUMAN_DECISION = "human_decision"
    HUMAN_ANNOTATION = "human_annotation"


class AuditActorType(str, enum.Enum):
    """Who performed the auditable action."""
    SYSTEM = "system"
    AGENT = "agent"
    HUMAN = "human"


class UserRole(str, enum.Enum):
    """RBAC roles."""
    COMPLIANCE_OFFICER = "compliance_officer"
    ADMINISTRATOR = "administrator"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class ProcessingStatus(str, enum.Enum):
    """Status of a raw event through the pipeline."""
    PENDING = "pending"
    SCREENING = "screening"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SCREENED_OUT = "screened_out"
