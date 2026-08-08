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
    is_operational_import = request.url.path == "/api/v1/workflows/import-json"
    # The import API carries JSON file text inside a JSON envelope. Escaping can
    # make the HTTP body approach twice the source-file size, so retain the
    # small global API limit while giving this one bounded endpoint headroom.
    request_limit = (
        settings.operational_import_max_bytes * 2 + 4096
        if is_operational_import
        else settings.max_request_bytes
    )
    if length > request_limit:
        message = (
            "Operational JSON files may be up to 10 MB."
            if is_operational_import
            else "Request exceeds the configured API size limit."
        )
        return JSONResponse(
            status_code=413,
            content={
                "code": "REQUEST_TOO_LARGE",
                "message": message,
                "production_action": "NOT_EXECUTED",
            },
        )
    now = time.monotonic(); key = request.client.host if request.client else "unknown"; bucket = _requests[key]
    while bucket and bucket[0] < now - 60: bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"code": "RATE_LIMITED", "production_action": "NOT_EXECUTED"})
    bucket.append(now); response = await call_next(request)
    response.headers.update({"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"no-referrer",
        "Permissions-Policy":"camera=(), microphone=(), geolocation=()","Content-Security-Policy":"default-src 'none'; frame-ancestors 'none'"})
    return response
