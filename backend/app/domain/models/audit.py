"""Audit Log ORM model — hash-chained, append-only, tamper-evident."""

from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable, hash-chained audit log entry.

    Every AI and human decision is written here. No record is ever
    mutated or deleted. Each entry's hash includes the previous entry's
    hash, forming a tamper-evident chain.

    Chain verification: hash(entry_n) includes hash(entry_n-1).
    If any entry is modified, the chain breaks from that point forward.
    """

    __tablename__ = "audit_log"

    # What happened
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False, default="system")

    # What it pertains to
    entity_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    alert_id: Mapped[str] = mapped_column(String(36), nullable=True)
    sar_id: Mapped[str] = mapped_column(String(36), nullable=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=True)

    # Details
    details: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Hash chain (tamper evidence)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="GENESIS")

    __table_args__ = (
        Index("ix_audit_log_entity_action", "entity_id", "action"),
        Index("ix_audit_log_created", "created_at"),
    )
