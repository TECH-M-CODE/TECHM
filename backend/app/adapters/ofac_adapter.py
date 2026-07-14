import json
import logging
from typing import Any
from pathlib import Path
from . import FeedAdapter

logger = logging.getLogger("sentinelai.adapters.ofac")

class OfacAdapter(FeedAdapter):
    """Adapter for OFAC sanctions updates.
    For local development, reads from a mock JSON file in the data directory.
    """
    def __init__(self, data_dir: str):
        self.data_file = Path(data_dir) / "mock_ofac_feed.json"

    async def fetch_events(self) -> list[dict[str, Any]]:
        if not self.data_file.exists():
            logger.warning(f"OFAC mock file not found: {self.data_file}")
            return []
            
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
            # Assuming data is a list of events
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error("Failed to parse OFAC mock data", exc_info=e)
            return []
