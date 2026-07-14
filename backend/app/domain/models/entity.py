"""Entity ORM model — monitored companies and individuals."""

from __future__ import annotations

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Entity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A monitored entity (company, individual, or financial institution).

    This is the central node in the KYC graph. Risk scores, alerts, SARs,
    and audit entries all link back to an entity.
    """

    __tablename__ = "entities"

    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")

    # KYC profile fields
    country: Mapped[str] = mapped_column(String(5), nullable=False, default="")
    sector: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    sector_risk: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    pep_flag: Mapped[bool] = mapped_column(default=False)
    sanctions_flag: Mapped[bool] = mapped_column(default=False)
    fatf_country_flag: Mapped[bool] = mapped_column(default=False)

    # Risk scoring (cumulative, deterministic)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_band: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    previous_risk_band: Mapped[str] = mapped_column(String(20), nullable=False, default="low")

    # Metadata
    aliases: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    external_id: Mapped[str] = mapped_column(String(200), nullable=True, index=True)

    # Relationships
    alerts = relationship("Alert", back_populates="entity", lazy="dynamic")
    risk_events = relationship("RiskEvent", back_populates="entity", lazy="dynamic")
    sar_drafts = relationship("SARDraft", back_populates="entity", lazy="dynamic")

    __table_args__ = (
        Index("ix_entities_risk_band", "risk_band"),
        Index("ix_entities_country", "country"),
        Index("ix_entities_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Entity(id={self.id!r}, name={self.name!r}, risk_band={self.risk_band!r})>"


class EntityPerson(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Relationship between entities (shared directors, UBOs, related parties).

    Used for indirect exposure propagation: when entity A is scored,
    related entity B receives a dampened score bump.
    """

    __tablename__ = "entity_persons"

    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    related_entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    person_name: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    __table_args__ = (
        Index("ix_entity_persons_pair", "entity_id", "related_entity_id"),
    )
