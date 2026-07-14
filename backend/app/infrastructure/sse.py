"""Server-Sent Events (SSE) broadcaster.

Pushes real-time updates to connected dashboard clients.
Event types: alert.new, alert.updated, sar.ready, entity.risk_changed

Uses asyncio.Queue per connected client. Client reconnect is handled
by the browser's EventSource auto-retry mechanism.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)


class SSEBroadcaster:
    """Manages SSE client connections and broadcasts events.

    Each connected client gets its own asyncio.Queue.
    Broadcasting pushes the event into every active queue.
    """

    def __init__(self) -> None:
        self._clients: list[asyncio.Queue[str]] = []
        self._event_count = 0

    @property
    def client_count(self) -> int:
        return len(self._clients)

    def connect(self) -> asyncio.Queue[str]:
        """Register a new client and return its event queue."""
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        self._clients.append(queue)
        logger.info("SSE client connected (total: %d)", self.client_count)
        return queue

    def disconnect(self, queue: asyncio.Queue[str]) -> None:
        """Remove a client's event queue."""
        if queue in self._clients:
            self._clients.remove(queue)
            logger.info("SSE client disconnected (total: %d)", self.client_count)

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast an event to all connected clients.

        Args:
            event_type: One of alert.new, alert.updated, sar.ready, etc.
            data: JSON-serializable event payload.
        """
        self._event_count += 1
        message = self._format_sse(event_type, data)

        disconnected: list[asyncio.Queue[str]] = []
        for queue in self._clients:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("SSE client queue full — dropping event")
                disconnected.append(queue)

        for queue in disconnected:
            self.disconnect(queue)

        logger.debug(
            "Broadcast event '%s' to %d clients (total events: %d)",
            event_type, self.client_count, self._event_count,
        )

    async def event_stream(self, queue: asyncio.Queue[str]) -> AsyncGenerator[str, None]:
        """Async generator yielding SSE-formatted events for a single client."""
        try:
            while True:
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            pass

    @staticmethod
    def _format_sse(event_type: str, data: dict[str, Any]) -> str:
        """Format data as an SSE message string."""
        payload = json.dumps(data, default=str)
        return f"event: {event_type}\ndata: {payload}\n\n"


# Global broadcaster instance
sse_broadcaster = SSEBroadcaster()
