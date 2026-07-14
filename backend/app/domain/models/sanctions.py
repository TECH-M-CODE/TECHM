"""Sanctions Cache ORM model — versioned, diff-based sanctions data."""

from __future__ import annotations

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SanctionsEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cached sanctions list entry with versioning.

    Sanctions lists are refreshed via diff-based updates:
    old rows get valid_to set, new rows are inserted with the
    new list_version. This preserves full history for audit.
    """

    __tablename__ = "sanctions_cache"

    # Source identification
    source_list: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(200), nullable=False)
    list_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Entity data
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    aliases: Mapped[str] = mapped_column(Text, nullable=False, default="")
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    date_of_birth: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    nationality: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    countries: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    addresses: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Sanctions program details
    sanction_program: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    identifiers: Mapped[str] = mapped_column(Text, nullable=False, default="")
    remarks: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Versioning (for diff-based refresh)
    valid_from: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    valid_to: Mapped[str] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)

    __table_args__ = (
        Index("ix_sanctions_source_active", "source_list", "is_active"),
        Index("ix_sanctions_name_active", "name", "is_active"),
    )


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Application user for authentication and RBAC."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(default=True)
