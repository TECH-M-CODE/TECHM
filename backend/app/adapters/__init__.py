from abc import ABC, abstractmethod
from typing import Any

class FeedAdapter(ABC):
    """Abstract Base Class for all ingestion feed adapters.
    
    Adapters are responsible for connecting to external sources (APIs, Webhooks,
    SFTP drops), fetching new data, and mapping it into a generic raw dictionary
    format that the IngestionService can process.
    """

    @abstractmethod
    async def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch new events from the feed.
        
        Returns:
            A list of raw event dictionaries.
        """
        ...
