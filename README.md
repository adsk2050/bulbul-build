# Bulbul Build

Indian voice toys made with Sarvam's [Bulbul V4 Flash](https://www.sarvam.ai/blogs/bulbul-v4-flash)
text-to-speech, plus Sarvam's LLM where a script needs writing or translating.

| Toy | What it does |
|---|---|
| **Talking Bulbul 🐦** (`/talk`) | Mitthu the bulbul repeats everything you say. Sharma uncle answers, cuts in and covers Mitthu's beak, live on Bulbul V4 Flash. Share any exchange as a video. |
| **Udhaar Wapas 💸** | A very polite "recovery desk" voice note for the friend who still owes you money, in 10 Indian languages, with a phone-line version. |

More toys land one by one.

## Run it

```bash
cp .env.example .env        # add your SARVAM_API_KEY
uv run bulbul-build         # http://127.0.0.1:8570
uv run bulbul-budget        # what has been spent
uv run pytest               # Sarvam is mocked; costs nothing
```

## Cost control

Every Sarvam call is reserved against daily and total caps in a local SQLite
ledger *before* it is sent, and settled with real usage after. Identical TTS
requests are served from a disk cache. Each IP is rate limited.
