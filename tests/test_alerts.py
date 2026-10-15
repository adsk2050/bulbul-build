"""Alerts: which spend alerts are due, once each; problems throttled. No network."""

from __future__ import annotations

import asyncio
import logging

from bulbul_build.alerts import ProblemLog, due
from bulbul_build.budget import Caps, Ledger


def spend(ledger: Ledger, inr: float) -> None:
    """Spend `inr` in calls no bigger than the per-call cap, as real use would."""
    while inr > 1e-9:
        part = min(inr, ledger.caps.per_call_inr)
        call = ledger.reserve("tts", "test", part, 1)
        ledger.settle(call, part, 1, "ok")
        inr -= part


def test_every_10_rupees_then_the_cap(tmp_path):
    ledger = Ledger(tmp_path / "l.sqlite", Caps(daily_inr=40, total_inr=1000, per_call_inr=2))
    sent: set[str] = set()
    assert due(ledger, sent) == []
    spend(ledger, 12)
    [(key, msg)] = due(ledger, sent)
    assert key.endswith(":10") and "Rs 12.00 spent today" in msg
    sent.add(key)
    assert due(ledger, sent) == []  # once only
    spend(ledger, 15)  # 27: the 20 step
    [(key, _)] = due(ledger, sent)
    assert key.endswith(":20")
    sent.add(key)
    spend(ledger, 11)  # 38 of 40: the next Rs 2 call would be refused
    [(key, msg)] = due(ledger, sent)
    assert key.endswith(":cap") and "quiet until midnight" in msg


def test_total_alert_at_80_percent(tmp_path):
    ledger = Ledger(tmp_path / "l.sqlite", Caps(daily_inr=100, total_inr=10, per_call_inr=10))
    spend(ledger, 8.1)
    assert "total:80" in [k for k, _ in due(ledger, set())]


def test_problems_are_throttled_per_kind():
    async def go():
        q: asyncio.Queue = asyncio.Queue()
        h = ProblemLog(q, asyncio.get_running_loop())
        lg = logging.getLogger("bulbul.test-alerts")
        lg.addHandler(h)
        try:
            for _ in range(3):
                lg.warning("commentary LLM failed: 500")
            lg.warning("reel join failed: bad file")
            lg.info("fine")
            await asyncio.sleep(0)
        finally:
            lg.removeHandler(h)
        return [q.get_nowait() for _ in range(q.qsize())]

    got = asyncio.run(go())
    assert len(got) == 2 and "LLM failed" in got[0] and "reel join" in got[1]
