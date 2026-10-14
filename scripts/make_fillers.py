"""Record the uncle's fillers and fallback lines once, into data/uncle/<id>.wav.

Costs money on the first run (Bulbul TTS); reruns are free from the TTS cache.
`--dry-run` only counts characters and the estimated cost.
Run: uv run python scripts/make_fillers.py [--dry-run]
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bulbul_build import config  # noqa: E402
from bulbul_build.budget import Caps, Ledger, cost_of  # noqa: E402
from bulbul_build.sarvam import Sarvam  # noqa: E402
from bulbul_build.uncle import FILLER_VOICE, RECORDED  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data" / "uncle"


async def main() -> None:
    chars = sum(len(c.text) for c in RECORDED)
    print(f"{len(RECORDED)} clips, {chars} chars, at most Rs {cost_of('tts', chars):.2f} (less if cached)")
    if "--dry-run" in sys.argv:
        return
    s = config.load()
    ledger = Ledger(s.ledger_path, Caps(s.daily_budget_inr, s.total_budget_inr, s.per_call_budget_inr))
    sarvam = Sarvam(s.sarvam_api_key, ledger, s.cache_dir)
    OUT.mkdir(parents=True, exist_ok=True)
    speaker, lang = FILLER_VOICE
    before = ledger.spent()
    try:
        for clip in RECORDED:
            wav = await sarvam.tts(clip.text, lang, speaker, mode="talking-bulbul-fillers")
            (OUT / f"{clip.id}.wav").write_bytes(wav)
            print("ok", clip.id, clip.text)
    finally:
        await sarvam.aclose()
    print(f"spent Rs {ledger.spent() - before:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
