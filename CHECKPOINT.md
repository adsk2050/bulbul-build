# CHECKPOINT — Talking Bulbul research (2026-10-14)

Session: 2808c301-26c1-4e09-b8e7-28259bbe29a2

## Decided (do not relitigate)
- New entry for the Bulbul Build Challenge (deadline 2026-10-15 20:00 IST):
  **a talking bulbul bird on its owner's palm**, in the website (this repo's app).
  Bird repeats you, Talking Tom style. The owner barges in sometimes, as
  character-driven guardrails (abuse, OTP/personal info, real questions,
  other languages). Exact rules still open.
- Must show Flash's **speed**: instant repeat, owner interrupts mid-word.
- Animation must look production quality, so it could become an app later.
- Form-based modes are not the entry. Bulbul Lab moved to the personal website
  (handoff: D:\personal-website\tmp\handoffs\2026-10-14-interactive-speech-blog.md).
- No paid calls without the user's yes (Sarvam, OpenAI image gen).

## Research (output: docs/research/talking-bulbul/)
| Agent | File | Status |
|---|---|---|
| research-animation | animation.md | done |
| research-voice-loop | voice-loop.md | done |
| research-character | character-design.md | done |

## Decided after research (2026-10-14 ~23:00)
- **Bird = the user's own recorded voice, replayed at ~1.35x** in the browser
  (no API). Bird may sometimes speak via TTS too (same path, pitched up).
- **Uncle = STT → LLM decision → Bulbul TTS.** He can step in on any turn,
  not only guardrails. Server applies frequency rules (guardrails always,
  comedy capped + cooldown); LLM writes the line.
- **Filler plays the moment the barge-in is decided**; the uncle's real TTS
  is generated in parallel and queued after it. Filler bank: 4–6 variants per
  situation, never the same twice in a row.
- Measured (docs/research/talking-bulbul/voice-loop.md, end): STT final
  ~650 ms after speech end, LLM ~200 ms, TTS first audio ~300 ms (WS kept
  open or HTTP stream). Uncle line ≈ 1.2 s, filler ≈ 0.85 s.
- Daily cap raised to Rs 40 (user OK). Art via OpenAI image gen approved
  (~$1–4); check price first.
- Placeholder art first; real art when ready.

## Next
1. DONE: research summary; latency measured; 36 uncle clips recorded (data/uncle/).
2. DONE (first cut): /talk page + /ws/talk. Files: talk.py, uncle.py,
   web/talk.{html,js,css}, web/mic-worklet.js, scripts/make_fillers.py.
3. User to try /talk in Chrome; tune VAD, barge timing, uncle frequency.
4. Character art (OpenAI images, check price) to replace the canvas placeholder.
5. Share video (canvas + audio -> MP4), hosting, entry video.
