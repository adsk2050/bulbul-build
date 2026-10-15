"""Spend alerts: which ones are due, once each. No network."""

from __future__ import annotations

from bulbul_build.alerts import due
from bulbul_build.budget import Caps, Ledger


def spend(ledger: Ledger, inr: float) -> None:
    """Spend `inr` in calls no bigger than the per-call cap, as real use would."""
    while inr > 1e-9:
        part = min(inr, ledger.caps.per_call_inr)
        call = ledger.reserve("tts", "test", part, 1)
        ledger.settle(call, part, 1, "ok")
        inr -= part


def test_half_then_cap_then_total(tmp_path):
    ledger = Ledger(tmp_path / "l.sqlite", Caps(daily_inr=10, total_inr=20, per_call_inr=1))
    sent: set[str] = set()
    assert due(ledger, sent) == []
    spend(ledger, 5.5)
    [(key, msg)] = due(ledger, sent)
    assert key.endswith(":50") and "Half" in msg
    sent.add(key)
    assert due(ledger, sent) == []  # once only
    spend(ledger, 3.8)  # 9.3 of 10: the next Rs 1 call would be refused
    [(key, msg)] = due(ledger, sent)
    assert key.endswith(":100") and "quiet until midnight" in msg


def test_total_alert_at_80_percent(tmp_path):
    ledger = Ledger(tmp_path / "l.sqlite", Caps(daily_inr=100, total_inr=10, per_call_inr=10))
    spend(ledger, 8.1)
    keys = [k for k, _ in due(ledger, set())]
    assert "total:80" in keys
