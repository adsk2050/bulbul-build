"""Alerts to the owner's phone, through ntfy (https://ntfy.sh, free, no account).

Spend: a push at every Rs 10 spent today, when the daily cap is reached (the
demos then go quiet until midnight IST), and once at 80 % of the total cap.
Problems: errors the app logs (Sarvam failing, a request that crashed), at most
once per kind per 10 minutes, and a push whenever the server starts, so a
restart after a crash shows up. A server that is down cannot say so itself:
the keep-warm GitHub job pushes to the same topic when the site does not answer.

Off unless NTFY_TOPIC is set. The topic name is the only secret: anyone who
knows it can read the alerts, so it lives in the host's settings, never in git.
"""

from __future__ import annotations

import asyncio
import logging
import time

import httpx

from .budget import Ledger

log = logging.getLogger("bulbul.alerts")
STEP_INR = 10
PROBLEM_GAP_S = 600  # the same kind of problem at most once per 10 minutes


def due(ledger: Ledger, sent: set[str]) -> list[tuple[str, str]]:
    """The spend alerts not yet sent, as (key, message); the caller adds each key to `sent`."""
    day = ledger._today()
    today, total = ledger.spent(day), ledger.spent()
    caps, out = ledger.caps, []
    # The ledger refuses a call that would pass the cap, so "reached" means less than
    # one call's worth is left.
    if today >= caps.daily_inr - caps.per_call_inr and f"{day}:cap" not in sent:
        out.append((f"{day}:cap", f"Daily cap reached: Rs {today:.2f} of Rs {caps.daily_inr:.0f}. "
                                  "The demos are quiet until midnight IST."))
    else:
        step = int(today // STEP_INR) * STEP_INR
        if step and f"{day}:{step}" not in sent:
            out.append((f"{day}:{step}", f"Rs {today:.2f} spent today (cap Rs {caps.daily_inr:.0f})."))
    if total >= 0.8 * caps.total_inr and "total:80" not in sent:
        out.append(("total:80", f"80% of the total cap spent: Rs {total:.2f} of Rs {caps.total_inr:.0f}."))
    return out


class ProblemLog(logging.Handler):
    """Queues the app's warnings and errors for a push, one per kind per PROBLEM_GAP_S."""

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        super().__init__(level=logging.WARNING)
        self.queue, self.loop = queue, loop
        self.last: dict[str, float] = {}

    def emit(self, record: logging.LogRecord) -> None:
        if record.name == log.name:
            return  # never alert about a failed alert
        kind = f"{record.name}:{record.getMessage()[:40]}"
        now = time.monotonic()
        if now - self.last.get(kind, -PROBLEM_GAP_S) < PROBLEM_GAP_S:
            return
        self.last[kind] = now
        text = f"{record.levelname} {record.name}: {record.getMessage()[:300]}"
        self.loop.call_soon_threadsafe(self.queue.put_nowait, text)


async def push(client: httpx.AsyncClient, topic: str, message: str, title: str, tags: str, priority: str = "default") -> None:
    await client.post(f"https://ntfy.sh/{topic}", content=message.encode(),
                      headers={"Title": title, "Tags": tags, "Priority": priority})


async def watch(ledger: Ledger, topic: str, every_s: float = 60.0) -> None:
    problems: asyncio.Queue[str] = asyncio.Queue()
    handler = ProblemLog(problems, asyncio.get_running_loop())
    watched = [logging.getLogger(n) for n in ("bulbul", "uvicorn.error")]
    for lg in watched:
        lg.addHandler(handler)
    sent: set[str] = set(k for k, _ in due(ledger, set()))  # nothing for spend already past at start
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await push(client, topic, "The server started (a deploy, or a restart after a crash).",
                           "Bulbul Build is up", "rocket", "low")
            except Exception as e:
                log.warning("alert failed: %s", e)
            while True:
                try:
                    for key, message in due(ledger, sent):
                        await push(client, topic, message, "Bulbul Build spend", "moneybag")
                        sent.add(key)
                    while not problems.empty():
                        await push(client, topic, problems.get_nowait(), "Bulbul Build problem", "warning", "high")
                except Exception as e:  # an alert must never take the app down
                    log.warning("alert failed: %s", e)
                await asyncio.sleep(every_s)
    finally:
        for lg in watched:
            lg.removeHandler(handler)
