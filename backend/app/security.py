import time
from collections import defaultdict, deque
from fastapi import Request
from fastapi.responses import JSONResponse
from .config import settings

_requests: dict[str, deque[float]] = defaultdict(deque)
def reset_rate_limits() -> None:
    _requests.clear()
async def security_middleware(request: Request, call_next):
    length = int(request.headers.get("content-length", "0") or 0)
    if length > settings.max_request_bytes:
        return JSONResponse(status_code=413, content={"code": "REQUEST_TOO_LARGE", "production_action": "NOT_EXECUTED"})
    now = time.monotonic(); key = request.client.host if request.client else "unknown"; bucket = _requests[key]
    while bucket and bucket[0] < now - 60: bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"code": "RATE_LIMITED", "production_action": "NOT_EXECUTED"})
    bucket.append(now); response = await call_next(request)
    response.headers.update({"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"no-referrer",
        "Permissions-Policy":"camera=(), microphone=(), geolocation=()","Content-Security-Policy":"default-src 'none'; frame-ancestors 'none'"})
    return response
