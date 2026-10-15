from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _f(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


@dataclass(frozen=True)
class Settings:
    sarvam_api_key: str
    port: int
    daily_budget_inr: float
    total_budget_inr: float
    per_call_budget_inr: float
    per_ip_per_min: int
    lines_per_ip_hour: int
    ledger_path: Path
    cache_dir: Path

    def __repr__(self) -> str:  # never print the key
        return f"Settings(port={self.port}, daily={self.daily_budget_inr}, total={self.total_budget_inr})"


def load() -> Settings:
    key = os.environ.get("SARVAM_API_KEY", "")
    return Settings(
        sarvam_api_key=key,
        port=int(os.environ.get("PORT", 8570)),
        daily_budget_inr=_f("DAILY_BUDGET_INR", 25),
        total_budget_inr=_f("TOTAL_BUDGET_INR", 50),
        per_call_budget_inr=_f("PER_CALL_BUDGET_INR", 2),
        per_ip_per_min=int(os.environ.get("PER_IP_PER_MIN", 6)),
        lines_per_ip_hour=int(os.environ.get("LINES_PER_IP_HOUR", 40)),
        ledger_path=Path(os.environ.get("LEDGER_PATH", ROOT / "data" / "ledger.sqlite")),
        cache_dir=Path(os.environ.get("CACHE_DIR", ROOT / "data" / "cache")),
    )
