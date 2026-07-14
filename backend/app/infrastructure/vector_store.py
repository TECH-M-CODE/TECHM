"""ChromaDB vector store wrapper.

Three collections as defined in the system design:
  - entity_cards: Entity profiles for semantic matching during resolution
  - event_context: Event snippets for RAG-based investigation
  - regulatory_corpus: Legal/regulatory text for SAR narrative generation

Designed so ChromaDB can later be swapped for Pinecone or pgvector.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ChromaDB import is deferred to avoid hard failure if not installed
_client = None
_collections: dict[str, Any] = {}

COLLECTION_NAMES = [
    "entity_cards",
    "event_context",
    "regulatory_corpus",
]


def get_chroma_client(persist_dir: str = "./data/chroma"):
    """Get or create the ChromaDB persistent client."""
    global _client
    if _client is None:
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            _client = chromadb.Client(ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_dir,
                anonymized_telemetry=False,
            ))
            logger.info("ChromaDB client initialized at %s", persist_dir)
        except ImportError:
            logger.warning("ChromaDB not installed — vector store disabled")
            return None
        except Exception as e:
            logger.warning("ChromaDB init failed: %s — using fallback", e)
            try:
                import chromadb
                _client = chromadb.PersistentClient(path=persist_dir)
                logger.info("ChromaDB PersistentClient initialized at %s", persist_dir)
            except Exception as e2:
                logger.error("ChromaDB PersistentClient also failed: %s", e2)
                return None
    return _client


def get_collection(name: str, persist_dir: str = "./data/chroma"):
    """Get or create a named ChromaDB collection."""
    if name not in COLLECTION_NAMES:
        raise ValueError(f"Unknown collection: {name}. Must be one of {COLLECTION_NAMES}")

    if name not in _collections:
        client = get_chroma_client(persist_dir)
        if client is None:
            return None
        _collections[name] = client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection '%s' ready", name)

    return _collections[name]


class VectorStore:
    """High-level wrapper around ChromaDB collections.

    Provides typed methods for embedding, querying, and managing
    the three core collections.
    """

    def __init__(self, persist_dir: str = "./data/chroma") -> None:
        self._persist_dir = persist_dir

    def _get_collection(self, name: str):
        return get_collection(name, self._persist_dir)

    async def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """Add documents to a collection."""
        collection = self._get_collection(collection_name)
        if collection is None:
            logger.warning("Vector store unavailable — skipping add to %s", collection_name)
            return

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.debug("Added %d documents to %s", len(documents), collection_name)

    async def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query a collection with semantic search."""
        collection = self._get_collection(collection_name)
        if collection is None:
            logger.warning("Vector store unavailable — returning empty results")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        kwargs: dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        return collection.query(**kwargs)

    async def delete(
        self,
        collection_name: str,
        ids: list[str],
    ) -> None:
        """Delete documents by ID."""
        collection = self._get_collection(collection_name)
        if collection is None:
            return
        collection.delete(ids=ids)

    async def count(self, collection_name: str) -> int:
        """Get document count in a collection."""
        collection = self._get_collection(collection_name)
        if collection is None:
            return 0
        return collection.count()


async def init_vector_store(persist_dir: str = "./data/chroma") -> VectorStore:
    """Initialize all ChromaDB collections."""
    store = VectorStore(persist_dir)
    for name in COLLECTION_NAMES:
        collection = store._get_collection(name)
        if collection is not None:
            count = collection.count()
            logger.info("Collection '%s': %d documents", name, count)
    return store
