# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# bulbul-build — repo guide

Indian voice toys on Sarvam's stack, built for Sarvam's Discord "Bulbul Build
Challenge" (deadline 2026-10-15 20:00 IST). The research behind the ideas is in
`D:\learn\speech\cs224s\experiments\exp007-bulbul-viral-build\reports\Bulbul GTM playbook and ideas.md`.

## Rules

- **Sarvam only.** TTS `bulbul:v4-flash`, LLM `sarvam-105b-conversations`
  (plain `sarvam-105b` spends its whole output budget on hidden reasoning and
  returns no text), translate, STT. All
  calls go through `src/bulbul_build/sarvam.py`, never raw HTTP from a mode.
- **Every paid call goes through the ledger** (`budget.py`): reserve the worst
  case before the call, settle after. Caps come from `.env`
  (`DAILY_BUDGET_INR`, `TOTAL_BUDGET_INR`, `PER_CALL_BUDGET_INR`).
  `uv run bulbul-budget` prints spend. Prices are list prices from
  sarvam.ai/api-pricing (2026-10-14); the launch promo is ignored on purpose.
- **Ask the user before any real Sarvam call** beyond what they approved.
  Tests mock Sarvam with respx and cost nothing.
- **The key never leaves the server.** `.env` is gitignored; gitleaks runs in
  pre-commit. Never print the key, not even its prefix.
- **Structured output** for LLM calls: `Sarvam.chat_json(..., schema=PydanticModel)`.
- `uv` only. `uv run pytest` before every commit.

## Commands

```bash
cp .env.example .env                 # then add SARVAM_API_KEY
uv run bulbul-build                  # http://127.0.0.1:8570
uv run bulbul-budget                 # spend so far
uv run pytest                        # all tests, Sarvam mocked
uv run pytest tests/test_family_ivr.py -k template   # one file / one test
```

`phone_line` output needs `ffmpeg` on PATH. `/api/budget` answers only from
localhost.

## Request flow

`POST /api/<slug>` → rate limit (per IP, `guard.py`) → validate the mode's
`Form` → `mode.build()` returns a `Script` → `ledger.check_headroom()` for the
whole script's TTS → each `Line` synthesised in parallel (4 at a time, cached
on disk by a hash of the request body) → WAVs joined with 250 ms gaps → captions timed
from clip lengths → optional 8 kHz phone version. Audio is served from
`data/cache/out/` by random token.

## Layout

| Path | What |
|---|---|
| `src/bulbul_build/app.py` | FastAPI server: page, `/api/modes`, `POST /api/<slug>`, `/audio/<id>.wav` |
| `src/bulbul_build/sarvam.py` | Sarvam client (tts with disk cache, chat_json, translate) |
| `src/bulbul_build/budget.py` | SQLite spend ledger and caps |
| `src/bulbul_build/modes/` | One module per idea; each exports `MODE` (see `base.py`) |
| `src/bulbul_build/web/` | One page for all modes; the form is built from the mode's pydantic schema |
| `data/` | ledger and audio cache (gitignored) |

## Writing a mode

Copy `modes/udhaar_wapas.py`. A mode is a pydantic `Form` plus an async
`build(form, sarvam) -> Script`. The server synthesises each `Line`, joins
them and draws the 9:16 card in the browser. **Register it by adding the
module name to `MODULES` in `modes/__init__.py`**; until then its route 404s
(tests that `monkeypatch` `REGISTRY` still pass, so they won't catch it).
Add a test in `tests/` with Sarvam mocked.

- **Voice IDs must be in `docs/voices-api.txt`** (the live API's list).
  `docs/voices.md` is Sarvam's doc page, which names voices the API rejects;
  `tests/test_voices.py` checks every mode against the API list.
- **Templates first, LLM only where needed.** Hindi, Hinglish and English are
  hand-written templates (free, exact). Other languages ask the LLM, then
  check the output with `script_share()` (`modes/base.py`) and fall back to a
  template if it is in the wrong script. The LLM drifts: it writes Hinglish
  in Latin letters, Marathi as Hindi (same script; `dashanan_roast.py` has a
  word check), and lowercases names. Restore names after the LLM.
- Hindi in Devanagari, English in Latin script; romanised Hindi sounds worse.
  Write numbers the TTS might misread (menu digits, train numbers) as words.
- Keep scripts short: a shareable clip is ~25 s.

## Ports — this repo owns 8570–8579

| Port | Service |
|---|---|
| 8570 | app (API and page) |
| 8571–8579 | free |
