"""Print each Talking Bulbul turn with its timings, from data/talk-log.jsonl.

Times are ms from the end of the visitor's speech (negative = while still talking).
Server and browser clocks are separate; each is measured from its own end of speech.
Run: uv run python scripts/talk_timings.py [last-N-turns]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LOG = Path(__file__).resolve().parents[1] / "data" / "talk-log.jsonl"
SERVER = ["first_partial", "barge", "final", "llm_done", "tts_first_audio", "tts_done"]
CLIENT = ["mitthu_start", "barge_received", "cover", "mitthu_cut", "mitthu_end_planned", "chacha_audio_start", "chacha_audio_end"]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    turns: dict[tuple, dict] = {}
    for line in LOG.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        key = (r["session"], r.get("turn"))
        t = turns.setdefault(key, {})
        kind = r.get("kind")
        if kind == "server_timing":
            t["server"] = r["ms"]
        elif kind == "client_timing":
            t["client"] = r["ms"] or {}
        else:
            t.update(r)
    for (session, turn), t in list(turns.items())[-n:]:
        print(f"{session} #{turn} [{t.get('situation')}] {t.get('visitor', '')!r} -> {t.get('chacha')!r}")
        s, c = t.get("server", {}), t.get("client", {})
        print("   server:", "  ".join(f"{k}={s[k]}" for k in SERVER if k in s))
        print("   browser:", "  ".join(f"{k}={c[k]}" for k in CLIENT if k in c))


if __name__ == "__main__":
    main()
