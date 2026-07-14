"""Alert ORM model — actionable risk alerts for compliance officers."""

from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Alert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An actionable alert raised from the risk pipeline.

    Alerts are created when an entity's risk score crosses a band threshold
    or when velocity exceeds the configured limit. Every alert requires
    human disposition (review → dismiss/escalate).
    """

    __tablename__ = "alerts"

    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    risk_event_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Classification
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="new")

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_bundle: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # AI reasoning
    ai_reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_confidence: Mapped[str] = mapped_column(String(10), nullable=False, default="0.0")

    # Human review
    assigned_to: Mapped[str] = mapped_column(String(36), nullable=True)
    reviewed_by: Mapped[str] = mapped_column(String(36), nullable=True)
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    disposition: Mapped[str] = mapped_column(String(30), nullable=True)

    # Drill flag
    is_drill: Mapped[bool] = mapped_column(default=False)

    # Relationship
    entity = relationship("Entity", back_populates="alerts")

    __table_args__ = (
        Index("ix_alerts_status_priority", "status", "priority"),
        Index("ix_alerts_entity_status", "entity_id", "status"),
    )
