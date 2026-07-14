import json
import hashlib
import logging
from typing import Callable, AsyncGenerator

from app.domain.interfaces import IUnitOfWork, IMessageBroker
from app.adapters import FeedAdapter
from app.infrastructure.telemetry import set_trace_id
import uuid

logger = logging.getLogger("sentinelai.services.ingestion")

class IngestionService:
    def __init__(
        self,
        uow_factory: Callable[[], AsyncGenerator[IUnitOfWork, None]],
        broker: IMessageBroker,
        adapters: list[FeedAdapter]
    ):
        # We take a factory because IngestionService might run as a background task
        # and needs to spawn its own UoW contexts per batch.
        self.uow_factory = uow_factory
        self.broker = broker
        self.adapters = adapters

    def _hash_content(self, payload: dict) -> str:
        # Sort keys to ensure consistent hashing
        content_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(content_str.encode("utf-8")).hexdigest()

    async def poll_all(self) -> int:
        """Polls all adapters, deduplicates, and enqueues new events."""
        trace_id = f"ingest-{uuid.uuid4().hex[:8]}"
        set_trace_id(trace_id)
        
        total_ingested = 0
        for adapter in self.adapters:
            events = await adapter.fetch_events()
            if not events:
                continue

            # We create a single unit of work per adapter batch
            uow_gen = self.uow_factory()
            uow = await anext(uow_gen)
            
            async with uow:
                for event_payload in events:
                    content_hash = self._hash_content(event_payload)
                    
                    exists = await uow.raw_events.exists_by_hash(content_hash)
                    if not exists:
                        # Create RawEvent
                        raw_event = await uow.raw_events.create({
                            "content_hash": content_hash,
                            "content": json.dumps(event_payload),
                            "processing_status": "pending"
                        })
                        # Must commit to get the ID if we use UUID PKs with defaults
                        # Actually wait, SQLAlchemy creates the ID locally if we defined a default, 
                        # but it's safer to wait until after commit to publish, OR publish the hash.
                        
                        # We won't publish here directly inside the loop because we haven't committed.
                        # Instead, we will commit at the end of the batch, then the pipeline polling 
                        # mechanism can pick up "pending" events. 
                        # OR we can just let the broker know that *something* arrived.
                        pass
                        
                await uow.commit()
                total_ingested += len(events)
            
            # Clean up generator
            try:
                await anext(uow_gen)
            except StopAsyncIteration:
                pass

        if total_ingested > 0:
            logger.info(f"Ingested {total_ingested} potential new events across {len(self.adapters)} adapters.")
            # Notify the screening pipeline that new events are available
            await self.broker.publish("pipeline.trigger", {"action": "screen_pending"})

        return total_ingested
