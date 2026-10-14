"""Per-IP rate limit, in memory. Good for one process; that is all we run."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request


class RateLimiter:
    def __init__(self, per_min: int, trust_proxy: bool = False):
        self.per_min = per_min
        self.trust_proxy = trust_proxy
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def client_ip(self, request: Request) -> str:
        if self.trust_proxy:
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def allow(self, ip: str) -> bool:
        now = time.monotonic()
        q = self._hits[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_min:
            return False
        q.append(now)
        return True
