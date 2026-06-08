"""FastAPI 中间件：请求追踪。"""

from __future__ import annotations

import time
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """为每个请求添加 trace_id 和耗时记录。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("x-trace-id", str(uuid.uuid4())[:8])
        request.state.trace_id = trace_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000

        response.headers["x-trace-id"] = trace_id
        response.headers["x-response-time-ms"] = f"{elapsed:.1f}"

        logger.info(
            "%s %s -> %s (%.1fms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
            trace_id,
        )
        return response
