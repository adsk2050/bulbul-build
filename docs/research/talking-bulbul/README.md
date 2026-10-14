# Talking Bulbul — research summary (2026-10-14)

Details and sources: `character-design.md`, `animation.md`, `voice-loop.md`.

## The product
Mitthu, a red-whiskered bulbul, sits on Sharma uncle's palm. Mitthu repeats
you instantly in a squeaky voice. The uncle is the straight man and barges in,
often mid-word. Humour comes from fixed rules, timing and 2–3 written
variants per line, not from LLM jokes.

## First six scenes
| # | Trigger | Detected by |
|---|---|---|
| 1 | Abuse: hand over the beak, escalates to the cage | word list on partial transcripts |
| 2 | OTP / phone number: bird starts reading it, uncle snatches it | regex |
| 3 | Real question: bird parrots, uncle sighs and answers in one line | LLM |
| 4 | Another language: uncle replies in it | STT language code |
| 5 | Same line three times: bird yawns | counter |
| 6 | Silence: bird pecks the screen, uncle coaxes (onboarding) | timer |

Guardrail scenes always fire. Comedy scenes at most 1 in 5 turns, 3-turn
cooldown, one guaranteed in the first 30 s.

## Voice loop
- Browser: one AudioContext; mic worklet sends 16 kHz PCM over a WebSocket;
  player worklet plays streamed PCM at ~1.35x for the bird (v4-flash ignores
  `pitch`), reports loudness for the beak, clears instantly on cut. Mic is
  muted while a character speaks + 400 ms (Chrome does not echo-cancel Web
  Audio playback).
- Server (FastAPI, one socket per session): `saaras:v3-realtime` STT,
  language `auto`; on final transcript, v4-flash TTS streams back. Regex and
  word list run on partials; risky words never reach the bird's TTS. LLM
  (`sarvam-105b-conversations`, JSON) only for questions and other languages.
  TTS has no cancel: close the stream and drop late chunks by utterance id.
- Expected: ~800 ms end of speech → bird audio (~550 ms with speculative TTS).
  End-of-turn detection dominates, so show Bulbul's own time-to-first-audio
  on screen. All Sarvam figures are vendor claims: measure first.

## Animation
- Target stack for the app: Rive (one .riv, state machine, beak blend 0–100,
  runs on web, iOS, Android, Flutter). Needs a human in the Rive editor.
- For the 20-hour build: layered image parts animated in code on a canvas;
  beak driven by loudness (fast open, slow close); idle breathing, blinks,
  "thinking" pose covers the wait.
- Share: MediaRecorder on canvas + audio, one server ffmpeg pass to
  H.264/AAC 9:16 MP4 under 16 MB, Web Share API with download fallback.

## Top risks
1. Art quality and rigging time.
2. Real latency vs Sarvam's claims.
3. iOS Safari: audio unlock, earpiece routing once the mic is open, canvas
   recording.
4. Barge-in audio control (beak freezing open on cut).
5. Rate limits: 105b at 40/min caps LLM decisions; regex pre-filter matters.
