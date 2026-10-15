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

## Talking Bulbul (`/talk`, the challenge entry)

Mitthu the bulbul parrots the visitor (their own recording, pitched up, in the
browser, free); Sharma uncle ("Chacha") answers or cuts in with live Bulbul.
`talk.py` is the per-visitor WebSocket session, `uncle.py` the rules, persona
and fillers, `web/talk.js` the mic, VAD, playback, sprites and share clip.

- The abuse word list is **not in git**: `private/abuse.txt` (gitignored; one
  term per line, `re:` for regexes; `ABUSE_FILE` overrides). Without it the
  abuse rule is off. Its real test cases: `uv run pytest private/`. Never
  commit curse words, in code, tests or commit messages.
- Fillers are recorded once: `uv run python scripts/make_fillers.py` (paid).
- Turns, transcripts and timings go to `data/talk-log.jsonl`;
  `uv run python scripts/talk_timings.py` prints them. What STT heard is in
  `data/utterances/`.
- Art: `scripts/make_art.py` (OpenAI images, paid; `build` step is free).

## Bulbul Flash Cricket (`/flash-cricket/`, the 3D game)

An open-source 3D batting game by ekcuttingchaidesign (upstream name "Hitman
Cricket") with Bulbul, the commentator, live on every ball. Earlier names
(`/hitman`, `/gully-bhaiya`) are gone on purpose: no redirects. Internal
names still say `hitman`: `web/hitman/` (the built game, committed),
`web/hitman-voice.js` (commentary socket, habits, match history),
`web/hitman-reel.js` (highlight reel and Share/Download), `cricket_rules/hitman.md`.

- **Rebuild:** `tools/hitman/build.sh <upstream checkout with npm ci>`. Our changes
  to the game live in `tools/hitman/bulbul-hooks.patch` plus `tools/hitman/bulbul.ts`;
  edit the checkout, then regenerate the patch from a pristine copy. The build
  empties upstream's offensive-word lists (`strip_wordlists.py`).
- **No board server:** the game runs offline (`canRegister: false`, `BULBUL_BUILD`
  flag, CSS in the patched `index.html` hides board features).
- **The reel** records each ball (canvas plus game audio) in the browser and cuts
  every four, six and wicket into a finished segment during play, Bulbul's line
  laid in whole from its PCM. At the end the best of the match (30 s max, last
  ball always in) plus an end card with a synthesised sting are joined two ways
  at once: `/api/reel` (ffmpeg, lossless copy, ~0.5 s, no re-encode ever) and a
  browser join (plays the segments into one recording); the first to finish wins.

## Public site (Render free web service)

`render.yaml` + `Dockerfile` (Render Blueprint, free plan, no card). The container
runs with `PUBLIC_SITE=1` (everything but the pixel game at `/cricket`; `/` is the
demo directory, `home.html`, with Bulbul Flash Cricket on top), `TRUST_PROXY=1`,
ledger and logs in `/tmp` (lost on restart: the total cap counts from the last
restart). `SARVAM_API_KEY` is set in Render's dashboard, never in git.
`.github/workflows/keep-warm.yml` visits every 10 min so the free service never
sleeps. Cost guards: `LINES_PER_IP_HOUR` (default 40) paid actions per IP per hour,
shared by commentary lines, Talking Bulbul turns and toy generations; and one ball
line per 2 s per connection. The visitor's IP comes from the rightmost `X-Forwarded-For` hop,
or from `CLIENT_IP_HEADER` if set; the log line `cricket ws ... -> counted as`
shows which, so check that two devices get different addresses.
