"""`uv run bulbul-budget` — print what has been spent, by day, service and mode."""

from __future__ import annotations

from . import config
from .budget import Caps, Ledger


def main() -> None:
    s = config.load()
    ledger = Ledger(s.ledger_path, Caps(s.daily_budget_inr, s.total_budget_inr, s.per_call_budget_inr))
    rows = ledger.report()
    print(f"{'day':<12}{'service':<11}{'mode':<22}{'calls':>6}{'units':>10}{'INR':>10}")
    for day, service, mode, n, units, inr in rows:
        print(f"{day:<12}{service:<11}{mode:<22}{n:>6}{units:>10.0f}{inr:>10.4f}")
    print(
        f"\ntoday Rs {ledger.spent(ledger._today()):.4f} of {s.daily_budget_inr:.2f}   "
        f"total Rs {ledger.spent():.4f} of {s.total_budget_inr:.2f}"
    )
