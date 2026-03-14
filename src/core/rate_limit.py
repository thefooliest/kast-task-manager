import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Simple in-memory rate limiter using a sliding window per IP."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup(self, ip: str, now: float) -> None:
        """Remove expired timestamps."""
        cutoff = now - self.window_seconds
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    def check(self, request: Request) -> None:
        """Raises 429 if rate limit is exceeded."""
        ip = self._get_client_ip(request)
        now = time.time()
        self._cleanup(ip, now)

        if len(self._requests[ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

        self._requests[ip].append(now)


# Login: max 10 attempts per minute
login_limiter = RateLimiter(max_requests=10, window_seconds=60)