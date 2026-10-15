"""Per-IP rate limit, in memory. Good for one process; that is all we run."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request


class RateLimiter:
    def __init__(self, per_min: int, trust_proxy: bool = False, ip_header: str = ""):
        self.per_min = per_min
        self.trust_proxy = trust_proxy
        # A header the host's edge sets to the visitor's address (e.g. cf-connecting-ip),
        # when X-Forwarded-For turns out to carry the proxy's own address.
        self.ip_header = ip_header.lower()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def client_ip(self, request: Request) -> str:
        if self.trust_proxy and self.ip_header and request.headers.get(self.ip_header):
            return request.headers[self.ip_header].strip()
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


def masked_chain(request: Request) -> str:
    """What the proxy headers carry, with addresses cut to their first half, for the log."""

    def cut(ip: str) -> str:
        ip = ip.strip()
        return ".".join(ip.split(".")[:2]) + ".x.x" if "." in ip else ip[:9] + "…"

    fwd = [cut(x) for x in (request.headers.get("x-forwarded-for") or "").split(",") if x.strip()]
    extra = {h: cut(request.headers[h]) for h in ("cf-connecting-ip", "true-client-ip", "x-real-ip") if request.headers.get(h)}
    peer = cut(request.client.host) if request.client else "?"
    return f"peer={peer} xff={fwd} {extra}"


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
