import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.infrastructure.telemetry import set_trace_id

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract trace_id from headers if passed by upstream, else generate
        trace_id = request.headers.get("x-trace-id") or uuid.uuid4().hex
        
        # Set ContextVar for python logging inside this request
        set_trace_id(trace_id)
        
        # Add to request state for endpoints to access
        request.state.trace_id = trace_id
        
        response = await call_next(request)
        
        # Always return trace_id to client for debugging
        response.headers["x-trace-id"] = trace_id
        return response
