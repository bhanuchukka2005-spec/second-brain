"""
In-memory sliding-window rate limiter.

Good enough for a single-process deployment (one uvicorn worker, which is
the default and what --reload uses). If you ever run multiple workers or
scale horizontally, this needs to move to Redis — each process would
otherwise track its own separate counts, weakening the limits.
"""
import time
import logging
import threading
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# key -> deque of request timestamps (seconds since epoch)
_buckets: Dict[str, Deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def _prune(bucket: Deque[float], window_seconds: int, now: float) -> None:
    """Drop timestamps older than the window from the left of the deque."""
    cutoff = now - window_seconds
    while bucket and bucket[0] < cutoff:
        bucket.popleft()


def check_rate_limit(key: str, max_requests: int, window_seconds: int) -> None:
    """
    Record a request for `key` and raise HTTP 429 if it exceeds
    `max_requests` within the trailing `window_seconds`.

    Call this at the top of a route handler (or from a dependency).
    """
    now = time.time()
    with _lock:
        bucket = _buckets[key]
        _prune(bucket, window_seconds, now)

        if len(bucket) >= max_requests:
            retry_after = int(window_seconds - (now - bucket[0])) + 1
            logger.warning(
                "Rate limit exceeded: key=%s limit=%d/%ds retry_after=%ds",
                key, max_requests, window_seconds, retry_after
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Too many requests. Please wait {retry_after}s before trying again."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)


def get_client_ip(request: Request) -> str:
    """
    Best-effort client IP extraction. Checks X-Forwarded-For first
    (set by reverse proxies like nginx/Railway/Render), falls back
    to the direct connection address.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For can be a comma-separated chain — the first
        # entry is the original client.
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def rate_limit_by_ip(max_requests: int, window_seconds: int):
    """
    Dependency factory for IP-based limiting — use on public endpoints
    that don't require auth yet (login, register, forgot-password).

    Usage:
        @router.post("/login", dependencies=[Depends(rate_limit_by_ip(5, 300))])
    """
    async def dependency(request: Request) -> None:
        ip = get_client_ip(request)
        check_rate_limit(f"ip:{request.url.path}:{ip}", max_requests, window_seconds)

    return dependency


def rate_limit_key_for_user(user_id: int, scope: str, max_requests: int, window_seconds: int) -> None:
    """
    Call this directly inside an authenticated route handler once you
    already have `current_user`, rather than adding a second Depends
    that would need to re-resolve the user.

    `scope` groups related endpoints under one shared budget, e.g. all
    of chat/ask and chat/ask/stream can share "chat" so a user can't
    dodge the limit by alternating between the two.
    """
    check_rate_limit(f"user:{user_id}:{scope}", max_requests, window_seconds)