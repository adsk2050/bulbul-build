"""Spend alerts to the owner's phone, through ntfy (https://ntfy.sh, free, no account).

Every minute the ledger is checked; a push goes out the first time today's spend
passes half the daily cap, when it reaches the cap (the demos then go quiet until
midnight IST), and once when the all-time spend passes 80 % of the total cap.
Off unless NTFY_TOPIC is set. The topic name is the only secret: anyone who
knows it can read the alerts, so it lives in the host's settings, never in git.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from .budget import Ledger

log = logging.getLogger("bulbul.alerts")


def due(ledger: Ledger, sent: set[str]) -> list[tuple[str, str]]:
    """The alerts not yet sent, as (key, message); the caller adds each key to `sent`."""
    day = ledger._today()
    today, total = ledger.spent(day), ledger.spent()
    caps, out = ledger.caps, []
    # The ledger refuses a call that would pass the cap, so "reached" means less than
    # one call's worth is left.
    if today >= caps.daily_inr - caps.per_call_inr and f"{day}:100" not in sent:
        out.append((f"{day}:100", f"Daily cap reached: Rs {today:.2f} of Rs {caps.daily_inr:.0f}. "
                                  "The demos are quiet until midnight IST."))
    elif today >= caps.daily_inr / 2 and f"{day}:50" not in sent:
        out.append((f"{day}:50", f"Half the daily cap spent: Rs {today:.2f} of Rs {caps.daily_inr:.0f}."))
    if total >= 0.8 * caps.total_inr and "total:80" not in sent:
        out.append(("total:80", f"80% of the total cap spent: Rs {total:.2f} of Rs {caps.total_inr:.0f}."))
    return out


async def watch(ledger: Ledger, topic: str, every_s: float = 60.0) -> None:
    sent: set[str] = set()
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                for key, message in due(ledger, sent):
                    await client.post(f"https://ntfy.sh/{topic}", content=message.encode(),
                                      headers={"Title": "Bulbul Build spend", "Tags": "moneybag"})
                    sent.add(key)
                    # A cap reached also covers the half-way alert it skipped.
                    if key.endswith(":100"):
                        sent.add(key[:-4] + ":50")
            except Exception as e:  # an alert must never take the app down
                log.warning("spend alert failed: %s", e)
            await asyncio.sleep(every_s)
