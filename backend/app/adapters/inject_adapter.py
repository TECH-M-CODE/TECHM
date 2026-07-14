from typing import Any
from . import FeedAdapter

class InjectAdapter(FeedAdapter):
    """A pass-through adapter for manual event injection via the API.
    Instead of polling, the API controller pushes data to this adapter,
    which then returns it when the pipeline asks.
    """
    def __init__(self):
        self._buffer: list[dict[str, Any]] = []

    def inject(self, event: dict[str, Any]) -> None:
        """Push an event into the adapter manually."""
        self._buffer.append(event)

    async def fetch_events(self) -> list[dict[str, Any]]:
        """Returns all injected events and clears the buffer."""
        events = self._buffer.copy()
        self._buffer.clear()
        return events
