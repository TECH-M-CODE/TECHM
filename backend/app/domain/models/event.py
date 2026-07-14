"""Event ORM models — raw events and scored risk events."""

from __future__ import annotations

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RawEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Normalized event from any feed adapter.

    All risk signals — adverse media, sanctions hits, transaction anomalies —
    are normalized into this single canonical structure. Deduplication is
    enforced by a SHA-256 content hash.
    """

    __tablename__ = "events_raw"

    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True,
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # Processing state
    processing_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True,
    )
    matched_entity_names: Mapped[str] = mapped_column(Text, nullable=False, default="")
    fuzzy_scores: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Drill flag — synthetic events from red-team drills
    is_drill: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        Index("ix_events_raw_status_created", "processing_status", "created_at"),
    )


class RiskEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A scored risk event linked to a resolved entity.

    Created after an event passes screening, entity resolution, and
    deterministic scoring. The score_delta is computed by the Scoring Engine
    using the formula: weight × severity × jurisdiction_multiplier.
    """

    __tablename__ = "risk_events"

    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    raw_event_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    score_delta: Mapped[float] = mapped_column(Float, nullable=False)
    score_after: Mapped[float] = mapped_column(Float, nullable=False)
    band_after: Mapped[str] = mapped_column(String(20), nullable=False)

    # Evidence and reasoning (from agents)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Source metadata
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # Indirect exposure tracking
    is_indirect: Mapped[bool] = mapped_column(default=False)
    source_entity_id: Mapped[str] = mapped_column(String(36), nullable=True)

    # Relationship
    entity = relationship("Entity", back_populates="risk_events")

    __table_args__ = (
        Index("ix_risk_events_entity_created", "entity_id", "created_at"),
    )
