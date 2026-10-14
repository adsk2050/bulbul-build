"""Spend ledger for every paid Sarvam call.

Every call is *reserved* before it is sent (worst-case estimate) and *settled*
after (actual units where the API reports them). A reservation that would push
spend past a cap is refused, so the caps hold even with concurrent requests.

Prices are Sarvam's pay-as-you-go list prices in INR, from
https://www.sarvam.ai/api-pricing (read 2026-10-14). The Bulbul V4 Flash launch
promo (Rs 10 per 10K chars until 2026-11-12) is ignored on purpose: the ledger
over-counts rather than under-counts.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))

# INR per unit.
PRICES = {
    "tts": 2.00 / 1000,  # per character, Bulbul V4 Flash
    "translate": 2.00 / 1000,  # per character
    "transliterate": 2.00 / 1000,  # per character
    "stt": 29.40 / 3600,  # per second of audio
    "llm_in": 15.00 / 1_000_000,  # per token, sarvam-105b
    "llm_out": 60.00 / 1_000_000,  # per token, sarvam-105b
}


class BudgetExceeded(RuntimeError):
    """Raised when a call would push spend past a cap."""


@dataclass(frozen=True)
class Caps:
    daily_inr: float
    total_inr: float
    per_call_inr: float


def cost_of(service: str, units: float) -> float:
    return PRICES[service] * units


def llm_cost(tokens_in: float, tokens_out: float) -> float:
    return cost_of("llm_in", tokens_in) + cost_of("llm_out", tokens_out)


class Ledger:
    def __init__(self, path: Path, caps: Caps):
        self.path = path
        self.caps = caps
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """create table if not exists calls (
                    id integer primary key,
                    ts real not null,
                    day text not null,
                    service text not null,
                    mode text not null,
                    units real not null,
                    inr real not null,
                    status text not null,
                    note text
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.execute("pragma journal_mode=wal")
        return db

    @staticmethod
    def _today() -> str:
        return datetime.now(IST).date().isoformat()

    def spent(self, day: str | None = None) -> float:
        """Spend including open reservations. `day=None` means all time."""
        with self._connect() as db:
            if day is None:
                row = db.execute("select coalesce(sum(inr),0) from calls").fetchone()
            else:
                row = db.execute(
                    "select coalesce(sum(inr),0) from calls where day=?", (day,)
                ).fetchone()
        return float(row[0])

    def check_headroom(self, est_inr: float) -> None:
        """Raise if `est_inr` more would pass a cap. Advisory: `reserve` is the real gate."""
        if self.spent() + est_inr > self.caps.total_inr:
            raise BudgetExceeded("total budget would be passed")
        if self.spent(self._today()) + est_inr > self.caps.daily_inr:
            raise BudgetExceeded("daily budget would be passed")

    def reserve(self, service: str, mode: str, est_inr: float, units: float) -> int:
        if est_inr > self.caps.per_call_inr:
            raise BudgetExceeded(
                f"one call would cost ~Rs {est_inr:.2f}, over the per-call cap "
                f"Rs {self.caps.per_call_inr:.2f}"
            )
        day = self._today()
        with self._lock, self._connect() as db:
            db.execute("begin immediate")
            try:
                total = db.execute("select coalesce(sum(inr),0) from calls").fetchone()[0]
                today = db.execute(
                    "select coalesce(sum(inr),0) from calls where day=?", (day,)
                ).fetchone()[0]
                if total + est_inr > self.caps.total_inr:
                    raise BudgetExceeded(
                        f"total budget Rs {self.caps.total_inr:.2f} would be passed "
                        f"(spent Rs {total:.2f})"
                    )
                if today + est_inr > self.caps.daily_inr:
                    raise BudgetExceeded(
                        f"daily budget Rs {self.caps.daily_inr:.2f} would be passed "
                        f"(spent today Rs {today:.2f})"
                    )
                cur = db.execute(
                    "insert into calls (ts, day, service, mode, units, inr, status) "
                    "values (?,?,?,?,?,?, 'reserved')",
                    (time.time(), day, service, mode, units, est_inr),
                )
                db.execute("commit")
                return int(cur.lastrowid)
            except BaseException:
                db.execute("rollback")
                raise

    def settle(self, call_id: int, inr: float, units: float, status: str, note: str = "") -> None:
        with self._lock, self._connect() as db:
            db.execute(
                "update calls set inr=?, units=?, status=?, note=? where id=?",
                (inr, units, status, note[:200], call_id),
            )

    def report(self) -> list[tuple]:
        with self._connect() as db:
            return db.execute(
                "select day, service, mode, count(*), round(sum(units)), round(sum(inr), 4) "
                "from calls group by day, service, mode order by day, service, mode"
            ).fetchall()
