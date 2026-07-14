import logging
from contextvars import ContextVar
from typing import Any

# Standard Python logger
logger = logging.getLogger("sentinelai")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s [Trace: %(trace_id)s]')
handler.setFormatter(formatter)
logger.addHandler(handler)

# ContextVar to hold trace_id for current request
current_trace_id: ContextVar[str | None] = ContextVar("current_trace_id", default=None)

class TelemetryFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = current_trace_id.get("N/A")
        return True

logger.addFilter(TelemetryFilter())

def log_info(message: str, **kwargs: Any) -> None:
    # In enterprise, this forwards to OTel collector. Here we just print structured logs.
    logger.info(f"{message} | kwargs: {kwargs}")

def log_error(message: str, exc: Exception | None = None, **kwargs: Any) -> None:
    logger.error(f"{message} | kwargs: {kwargs}", exc_info=exc)

def set_trace_id(trace_id: str) -> None:
    current_trace_id.set(trace_id)
