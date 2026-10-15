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
                # The rightmost entry is the one our proxy added; anything to its
                # left came from the client and can be made up.
                return fwd.split(",")[-1].strip()
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


class LineQuota:
    """Paid commentary lines per IP per hour, so one visitor (or one script)
    cannot spend the whole day's budget that everybody shares."""

    def __init__(self, per_hour: int):
        self.per_hour = per_hour
        self._lines: dict[str, deque[float]] = defaultdict(deque)

    def take(self, ip: str) -> bool:
        now = time.monotonic()
        q = self._lines[ip]
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= self.per_hour:
            return False
        q.append(now)
        return True
