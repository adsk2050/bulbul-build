# bulbul-build — repo guide

Indian voice toys on Sarvam's stack, built for Sarvam's Discord "Bulbul Build
Challenge" (deadline 2026-10-15 20:00 IST). The research behind the ideas is in
`D:\learn\speech\cs224s\experiments\exp007-bulbul-viral-build\reports\Bulbul GTM playbook and ideas.md`.

## Rules

- **Sarvam only.** TTS `bulbul:v4-flash`, LLM `sarvam-105b`, translate, STT. All
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
them and draws the 9:16 card in the browser. Voice IDs must come from the
v4-flash catalog (`docs/voices.md`). Hindi in Devanagari, English in Latin
script; romanised Hindi sounds worse. Add a test in `tests/` with Sarvam mocked.

## Ports — this repo owns 8570–8579

| Port | Service |
|---|---|
| 8570 | app (API and page) |
| 8571–8579 | free |
