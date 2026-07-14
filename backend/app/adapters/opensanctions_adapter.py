import json
import logging
from typing import Any
from pathlib import Path
from . import FeedAdapter

logger = logging.getLogger("sentinelai.adapters.opensanctions")

class OpenSanctionsAdapter(FeedAdapter):
    """Adapter for OpenSanctions data dumps.
    Reads from local JSONLines file for demonstration.
    """
    def __init__(self, data_dir: str):
        self.data_file = Path(data_dir) / "mock_opensanctions_feed.jsonl"

    async def fetch_events(self) -> list[dict[str, Any]]:
        if not self.data_file.exists():
            logger.warning(f"OpenSanctions mock file not found: {self.data_file}")
            return []
            
        events = []
        try:
            with open(self.data_file, "r") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
            return events
        except Exception as e:
            logger.error("Failed to parse OpenSanctions mock data", exc_info=e)
            return events
