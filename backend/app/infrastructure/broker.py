import asyncio
from typing import Any
from app.domain.interfaces import IMessageBroker

class AsyncioMessageBroker(IMessageBroker):
    """Local asyncio-based broker.
    For Phase 3/4 this will act as a simple in-memory queue.
    In enterprise deployment, swap for Redis PubSub or Celery/RabbitMQ."""

    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
        self._pubsub: dict[str, list[asyncio.Queue]] = {}

    def _get_pubsub_channel(self, channel: str) -> list[asyncio.Queue]:
        if channel not in self._pubsub:
            self._pubsub[channel] = []
        return self._pubsub[channel]

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        subscribers = self._get_pubsub_channel(channel)
        for sub_queue in subscribers:
            await sub_queue.put(message)

    async def subscribe(self, channel: str) -> asyncio.Queue:
        # Returns an asyncio queue that caller can await .get() on
        q = asyncio.Queue()
        self._get_pubsub_channel(channel).append(q)
        return q

    async def enqueue_task(self, queue: str, task: dict[str, Any]) -> None:
        if queue not in self._queues:
            self._queues[queue] = asyncio.Queue()
        await self._queues[queue].put(task)
