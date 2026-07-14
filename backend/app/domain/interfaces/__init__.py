"""Abstract repository interfaces.

These define the contract between the domain/service layer and
the persistence layer. Concrete implementations (SQLite, PostgreSQL)
live in app.repositories. This allows swapping storage backends
without touching business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IEntityRepository(ABC):
    """Interface for entity persistence operations."""

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Any | None:
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Any | None:
        ...

    @abstractmethod
    async def list_all(
        self, page: int = 1, page_size: int = 20, filters: dict[str, Any] | None = None,
    ) -> tuple[list[Any], int]:
        ...

    @abstractmethod
    async def update(self, entity_id: str, data: dict[str, Any]) -> Any | None:
        ...

    @abstractmethod
    async def update_risk_score(
        self, entity_id: str, new_score: float, new_band: str,
    ) -> Any | None:
        ...

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[Any]:
        ...

    @abstractmethod
    async def get_all_names(self) -> list[tuple[str, str]]:
        """Return all (entity_id, name) pairs for fuzzy screening."""
        ...


class IRawEventRepository(ABC):
    """Interface for raw event persistence."""

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def exists_by_hash(self, content_hash: str) -> bool:
        ...

    @abstractmethod
    async def get_unprocessed(self, limit: int = 50) -> list[Any]:
        ...

    @abstractmethod
    async def update_status(self, event_id: str, status: str) -> None:
        ...


class IRiskEventRepository(ABC):
    """Interface for scored risk event persistence."""

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def get_by_entity(
        self, entity_id: str, limit: int = 50,
    ) -> list[Any]:
        ...

    @abstractmethod
    async def get_recent_score_deltas(
        self, entity_id: str, days: int = 7,
    ) -> list[float]:
        """Get score deltas for velocity calculation."""
        ...


class IAlertRepository(ABC):
    """Interface for alert persistence."""

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def get_by_id(self, alert_id: str) -> Any | None:
        ...

    @abstractmethod
    async def list_all(
        self, page: int = 1, page_size: int = 20, filters: dict[str, Any] | None = None,
    ) -> tuple[list[Any], int]:
        ...

    @abstractmethod
    async def update(self, alert_id: str, data: dict[str, Any]) -> Any | None:
        ...


class ISARRepository(ABC):
    """Interface for SAR draft persistence."""

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def get_by_id(self, sar_id: str) -> Any | None:
        ...

    @abstractmethod
    async def list_all(
        self, page: int = 1, page_size: int = 20, filters: dict[str, Any] | None = None,
    ) -> tuple[list[Any], int]:
        ...

    @abstractmethod
    async def update(self, sar_id: str, data: dict[str, Any]) -> Any | None:
        ...

    @abstractmethod
    async def create_new_version(self, sar_id: str, data: dict[str, Any]) -> Any:
        """Create a new version of an existing SAR, preserving the old one."""
        ...


class IAuditRepository(ABC):
    """Interface for audit log persistence.

    Note: No update or delete methods. The audit log is append-only.
    """

    @abstractmethod
    async def append(self, data: dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def get_by_entity(
        self, entity_id: str, limit: int = 100,
    ) -> list[Any]:
        ...

    @abstractmethod
    async def get_chain(self, limit: int = 1000) -> list[Any]:
        """Get entries in chain order for verification."""
        ...

    @abstractmethod
    async def get_latest(self) -> Any | None:
        """Get the most recent entry (for chaining)."""
        ...

    @abstractmethod
    async def list_all(
        self, page: int = 1, page_size: int = 20, filters: dict[str, Any] | None = None,
    ) -> tuple[list[Any], int]:
        ...


class ISanctionsRepository(ABC):
    """Interface for sanctions cache persistence."""

    @abstractmethod
    async def upsert_batch(
        self, entries: list[dict[str, Any]], source_list: str, version: int,
    ) -> dict[str, int]:
        """Insert new entries, deactivate removed ones. Return diff counts."""
        ...

    @abstractmethod
    async def get_active_names(self, source_list: str | None = None) -> list[tuple[str, str]]:
        """Return all (id, name) pairs for active sanctions entries."""
        ...

    @abstractmethod
    async def search(self, name: str, limit: int = 10) -> list[Any]:
        ...

    @abstractmethod
    async def get_current_version(self, source_list: str) -> int:
        ...


class IUnitOfWork(ABC):
    """Context manager for atomic commits across repositories."""

    entities: IEntityRepository
    raw_events: IRawEventRepository
    risk_events: IRiskEventRepository
    alerts: IAlertRepository
    sars: ISARRepository
    audit: IAuditRepository
    sanctions: ISanctionsRepository

    @abstractmethod
    async def __aenter__(self) -> "IUnitOfWork":
        ...

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ...

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...


class ICacheProvider(ABC):
    """Interface for distributed or local caching."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def invalidate_tag(self, tag: str) -> None:
        ...


class IMessageBroker(ABC):
    """Interface for pub/sub message brokering."""

    @abstractmethod
    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        ...

    @abstractmethod
    async def subscribe(self, channel: str) -> Any:
        ...

    @abstractmethod
    async def enqueue_task(self, queue: str, task: dict[str, Any]) -> None:
        ...


class ISecretsManager(ABC):
    """Interface for secure secrets retrieval."""

    @abstractmethod
    def get_secret(self, key: str) -> str | None:
        ...
