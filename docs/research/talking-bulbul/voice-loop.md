# Talking Bulbul — voice loop research

Research for the talking-bird demo: user speaks, bird repeats in a pitched-up
voice, owner may barge in. Read 2026-10-14. Docs only; no Sarvam calls made.

Status: complete (2026-10-14).

## 1. Sarvam streaming APIs today

### Findings (raw, as read)

**Streaming STT — `saaras:v3-realtime` (new) over WebSocket**
- Endpoint `wss://api.sarvam.ai/speech-to-text-realtime/ws`, auth header
  `api-subscription-key`. Models `saaras:v3-realtime` (default) and `saaras:v4`.
  https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/realtime-streaming
- Query params: `language_code` (BCP-47 or `auto`), `stream_type`
  (`fast` / `balanced` default / `simulated` = no partials), `mode` (final only:
  `transcribe`, `translate`, `verbatim`, `translit`, `codemix`), `endpointing`
  (`vad` default / `manual`), `encoding` (`linear16` default, `linear32`,
  `mulaw`, `alaw`; mono), `sample_rate` 8000 or 16000 only, `threshold` 0.3,
  `silence_duration_ms` 500, `min_speech_duration_ms` 250, `return_timestamps`,
  `prompt`, `keyterms` (v4 only). Same source.
- Client sends `{"event":"audio_input","audio":"<base64>"}`; in manual mode also
  `speech_start`, `speech_end`, `flush` (force-finalise). Also `end`, `ping`,
  `config.update`. Same source.
- Server sends `session.begin`, `vad.speech_start`, `vad.speech_end`,
  `transcript.partial` (`text`, plus `language` when `auto`),
  `transcript.final` (`text`, `language`, `language_confidence` when `auto`),
  `session.end` (`audio_duration_s` = billed audio), `error`. Same source.
- `silence_duration_ms`, `threshold` can be changed mid-session and apply
  immediately. Close codes: 1003 rate/quota/key, 1008 inactivity (send ping),
  1011 internal, 4000 bad param. Same source.
- The page gives **no latency numbers** and no streaming price. Same source.
- Legacy WebSocket `saaras:v3` streaming still GA.
  https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/overview

**Streaming TTS — `bulbul:v4-flash`**
- Three ways: REST `/text-to-speech` (base64 WAV, what `sarvam.py` uses today),
  HTTP stream `POST /text-to-speech/stream`, WebSocket.
  https://docs.sarvam.ai/api/getting-started/models/bulbul
- HTTP stream returns raw binary audio (not base64/JSON), codec set by
  `output_audio_codec` (`mp3` default, `wav`, `aac`, `opus`, `flac`, `linear16`,
  `mulaw`, `alaw`), `speech_sample_rate` default 22050, max 3500 chars,
  `enable_preprocessing`, `enable_cached_responses` (beta). No TTFA number, no
  cancel or partial-billing statement.
  https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/streaming-api/http-stream
- Streaming sample rates: 8000, 16000, 22050, 24000 Hz. Pitch range listed
  -1.0..1.0 but v4-flash support not confirmed. Default speaker on v4-flash is
  `shubh_enhi_ads`. https://docs.sarvam.ai/api/getting-started/models/bulbul
- WebSocket: send `config` first (`speaker`, `language_code`, `pace`,
  `min_buffer_size`, `max_chunk_length`, `output_audio_codec`,
  `output_audio_bitrate`), then `{"type":"text","data":{"text":"..."}}`, then
  `{"type":"flush"}`; `{"type":"ping"}` keepalive. Audio comes back as
  `type:"audio"` with base64 at `data.audio`; `send_completion_event=true`
  gives a `final` event. 1–2500 chars per message, under 500 recommended.
  Idle close after about 1 minute.
  https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/streaming-api/web-socket
- **There is no cancel message.** Sarvam's own barge-in advice: stop local
  playback, close the TTS socket so the server stops generating, open a new
  one for the next reply; keep `convert()` calls short to limit waste.
  Same source.
- Launch claim: under 250 ms time-to-first-audio, up to 40% faster than V3,
  Rs 20 per 10K chars. https://www.sarvam.ai/blogs/bulbul-v4-flash (as
  collected in `D:\learn\speech\cs224s\experiments\exp007-bulbul-viral-build\research_notes\Viral Bulbul challenge ideas\bulbul_capabilities.md` line 9)
- Prior notes record the raw WS URL as `wss://api.sarvam.ai/text-to-speech/ws`
  and REST rate limits 60/200/1000 req/min, WS 60/200/1000 concurrent
  (Starter/Pro/Business). Same local file, lines 40, 51.

- **Raw TTS WS spec**: `wss://api.sarvam.ai/text-to-speech/ws?model=...&send_completion_event=true`,
  key in `Api-Subscription-Key` **header only** (no query-param auth), so a
  browser `WebSocket` cannot authenticate directly; a server proxy is required
  anyway. https://docs.sarvam.ai/api-reference/text-to-speech/stream.md
- Same spec: **`pitch` and `loudness` are ignored on v3 and v4-flash.** The
  bird's pitch-up must be done by us, after synthesis. `enable_preprocessing`
  is always on for v4-flash. `min_buffer_size` 30–200 (default 50),
  `max_chunk_length` 50–500 (default 150), `speech_sample_rate` "8000" /
  "16000" / "22050" / "24000", codecs include `linear16` (raw PCM).
  Server audio message: `{"type":"audio","data":{"content_type","audio","request_id"}}`.
  Same source.
- Sarvam's Pipecat guide recommends `min_buffer_size` 15–25 for faster first
  audio (conflicts with the 30 minimum in the spec; for our case we send whole
  short utterances followed by `flush`, so it does not matter).
  https://docs.sarvam.ai/api/integration/pipecat-production-guide

**STT latency claims (vendor only)**
- "Sub-150ms time to first token" in Realtime Fast mode; "<250ms Median
  latency"; Rs 1.5 per minute of audio. https://www.sarvam.ai/speech-to-text
- No independent latency benchmark found. smallest.ai lists Saaras WER 0.376
  on 44 Hindi-English collections calls (vs Deepgram Nova 3 0.325), no
  latency. https://smallest.ai/benchmarks
- Pipecat's Sarvam realtime service measures STT TTFB from local VAD stop,
  "because Sarvam's own speech-end event arrives only after its server-side
  silence window" (default `silence_duration_ms` 500). Its default
  `ttfs_p99_latency` is 1.0 s (realtime) / 1.17 s (legacy, measured with VAD
  stop 0.2 s). https://reference-server.pipecat.ai/en/latest/api/pipecat.services.sarvam.stt.html
- Pipecat's client buffers 500 ms of audio before sending in `fast` mode
  (1000 ms in `balanced`). That is a Pipecat choice, not an API rule; our proxy
  should forward 20–40 ms frames. https://docs.sarvam.ai/api/integration/pipecat-production-guide
- Barge-in in Sarvam's Pipecat setup: each `vad.speech_start` cuts bot audio
  by default; to ignore "haan"/"achha", gate with `MinWordsUserTurnStartStrategy(min_words=3, use_interim=True)`.
  Same source.

**LLM**
- `sarvam-105b` (128K ctx) and `sarvam-105b-conversations` (32K, "real-time
  dialogue and voice-agent workloads"). `stream: true` gives SSE with
  `delta.content` and `delta.reasoning_content`. Thinking is **on by default at
  `low`**; disable with `reasoning_effort: null`. Reasoning tokens are billed
  and can eat `max_tokens`. `response_format` `json_schema` with `strict: true`
  supported. No TTFT or tokens/s published.
  https://docs.sarvam.ai/api/api-guides-tutorials/chat-completion/overview
- V2 endpoint `POST /v2/chat/completions` hosts open-weight models (`gemma4`,
  `glm5.3`, `deepseekv4.1-flash`) in beta. These are hosted by Sarvam but not
  Sarvam-trained; whether they count as "Sarvam models" for the challenge is a
  call for us. Same source.
- Our client currently sends `reasoning_effort: "low"` to
  `sarvam-105b-conversations` (`D:\bulbul-build\src\bulbul_build\sarvam.py`
  line 126). For the barge-in classifier, set it to `null` and cap
  `max_tokens` at ~60.
- Rate limit for 105b models is the tightest of all: 40 req/min on Starter,
  60 Pro, 120 Business. https://docs.sarvam.ai/api/getting-started/ratelimits

**Translate**
- `mayura:v1` (11 langs, 1,000 chars, modes formal / modern-colloquial /
  classic-colloquial / code-mixed, `source_language_code: "auto"`) and
  `sarvam-translate:v1` (22 langs, 2,000 chars). No latency figures. No
  separate text language-ID API mentioned.
  https://docs.sarvam.ai/api/getting-started/models/mayura
- We do not need translate for language detection: realtime STT with
  `language_code=auto` returns `language` and `language_confidence` on
  `transcript.final`. https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/realtime-streaming

**Rate limits (per account, shared by all keys)**
- Starter: STT WS 20 concurrent, TTS WS 60 concurrent, TTS REST 60/min, chat
  60/min (105b: 40/min), translate 60/min. Rs 100 free credits on signup.
  WS bursts can be rejected with close 1003.
  https://docs.sarvam.ai/api/getting-started/ratelimits
- Consequence: 20 concurrent STT sockets caps the demo at about 20
  simultaneous users on Starter; the 105b limit (40/min) caps owner LLM
  decisions. The regex pre-filter matters for capacity, not only latency.

### Takeaway (Q1)
Everything we need exists: realtime STT over WS with partials, server VAD and
language auto-detect; v4-flash TTS over WS or HTTP stream with raw `linear16`
PCM. There is no TTS cancel message (close the socket) and no server pitch
control on v4-flash (pitch in the browser). The key must sit on our server,
since Sarvam WS auth is header-only.

### Gaps (Q1)
- No published STT or TTS latency except vendor claims (<150 ms STT first
  token, <250 ms TTS first audio). Measure on day one.
- Unknown whether a closed TTS socket is billed for the full text or only what
  was generated. Assume full text (reserve worst case).
- Unknown TTFT for `sarvam-105b-conversations` with reasoning off.
- STT price for realtime streaming not on the API docs; marketing page says
  Rs 1.5/min.

## 2. Latency budget

### Takeaway (Q2)
Realistic end of speech → first bird audio is about 600–900 ms; best case about
450 ms with tricks. Bulbul's own <250 ms is only part of that. Endpointing
(deciding the user has stopped) is the largest single cost, so show the
Bulbul TTFA as its own on-screen number. The owner's decision can be ready
**before** the user stops if it runs on partials.

### Findings
- **Interactive target**: lecture 9 puts the end-to-end budget at 200 ms.
  `D:\learn\speech\cs224s\notes\lec09\notes.md` line 111. The repeat path will
  not hit that; a repeat ("echo") is expected to come after the user stops, so
  ~0.5–0.8 s still reads as instant for a toy.
- **Endpointing dominates.** Sarvam realtime STT default `silence_duration_ms`
  is 500 ms; it can be lowered live.
  https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/realtime-streaming
  Pipecat measures Sarvam STT TTFB from local VAD stop because the server
  speech-end comes only after that silence window.
  https://reference-server.pipecat.ai/en/latest/api/pipecat.services.sarvam.stt.html
  Other vendors default to 100 ms silence (Deepgram `endpointing`, AssemblyAI
  `min_turn_silence`); OpenAI server VAD ~500 ms (community-sourced).
  `D:\learn\speech\cs224s\experiments\exp002-barge-in\research\e1-industry.md` §3.
- **STT final**: vendor claims "Sub-150ms time to first token" (Fast) and
  "<250ms Median latency". https://www.sarvam.ai/speech-to-text. Pipecat's
  default p99 time-to-final-segment for Sarvam is 1.0 s (realtime) / 1.17 s
  (legacy, measured). Pipecat reference above.
- **TTS first audio**: vendor "under 250 ms in production", no method given.
  https://www.sarvam.ai/blogs/bulbul-v4-flash. The user's exp001 found vendor
  TTS TTFB claims and measurements disagree badly: 37 ms claimed vs 313 ms
  measured for the same products; middle 80% of 17 reported figures is
  50–440 ms. `D:\learn\speech\cs224s\experiments\exp001-streaming-tts\README.md`
  ("What the latency knobs added").
- **Platform-reported latency runs ~490 ms below independent measurement**;
  independent median caller-stop → agent-audio on 5 production platforms is
  1,296–1,740 ms. openbenchmarks.com, via `exp002-barge-in\research\e1-industry.md` §5.1.
  So a full STT→LLM→TTS agent is ~1.3 s in practice; our repeat path skips
  the LLM, which is why it can be ~2x faster.
- **Stopping playback**: halting floor for humans ~194 ms; humans stop in
  287 ms median when overlapped, LLM agents 931 ms. Playback buffer in two
  sources is 50–60 ms. `D:\learn\speech\cs224s\experiments\exp002-barge-in\README.md`
  (Why it matters; hypothesis table row 5). With an AudioWorklet ring buffer
  we control the buffer, so the owner's cut can be ~20–60 ms (output latency).
- **Chunking lesson from exp001**: never synthesise below a clause; fragments
  inflate audio (token arm 4.9x longer) and break prosody. For the bird, send
  the whole utterance in one TTS call. `exp001-streaming-tts\README.md` Results.

### Budget (repeat path, end of user speech → first audible bird sample)

| Step | Plain | With tricks | Source / basis |
|---|---|---|---|
| Endpoint detect | 500 ms (Sarvam default) | 250–300 ms (local Silero `redemptionMs` 250–300, or `silence_duration_ms` 300) | Sarvam realtime docs; vad-web docs |
| STT final after endpoint | 150–300 ms | 0 (use last partial speculatively) | sarvam.ai/speech-to-text claim; unmeasured |
| Server → Sarvam TTS first chunk | 250–400 ms | 200–300 ms (pre-warmed socket/HTTP2 pool) | Bulbul blog claim; exp001 vendor-vs-measured gap |
| Our server ↔ browser (one way, India) | 30–60 ms | 30–60 ms | estimate; measure |
| Browser jitter buffer + output | 40–80 ms | 20–40 ms | exp002 README (50–60 ms); worklet buffer we choose |
| **Total** | **~950–1,350 ms** | **~500–700 ms** | |

### Budget (owner barge-in decision)

| Case | When the decision is ready | Basis |
|---|---|---|
| OTP / phone digits, known abuse word | On the partial that contains it, **before** end of speech (regex, ~0 ms) | `transcript.partial` events |
| Other language | On the first partial or final carrying `language` ≠ expected | `language` on partial/final when `language_code=auto` |
| Real question / ambiguous abuse | End of speech + LLM call (no published TTFT; guess 400–1,000 ms with reasoning off) | chat completion docs; unmeasured |
| Owner's first audio after decision | ~0 ms from a pre-cached interjection ("अरे रुको!"), then the LLM line via TTS | our disk TTS cache in `sarvam.py` |

The bird starts at ~0.6 s; an LLM-gated owner cut lands at ~1.2–1.8 s, i.e.
0.5–1 s into the bird's line. That reads as "cut off mid-word", which is the
joke. Regex cases can be decided before the bird even starts (see §4).

### Where we can cheat
1. **Speculative TTS on the last partial.** When local VAD says the user
   stopped, send the latest partial to TTS immediately. If the final differs,
   cancel and re-synthesise. Costs extra TTS chars on mismatches.
2. **Lower `silence_duration_ms` to 250–300** (live-updatable) or drive
   endpointing from the browser VAD in `manual` mode (`speech_end` + `flush`).
3. **Pre-warmed connections.** Keep a TTS WS open per voice with `config`
   already sent, `ping` every <60 s; or an httpx HTTP/2 pool for
   `/text-to-speech/stream`. Saves TLS + handshake on every turn.
4. **Cached owner interjections** per language, synthesised once at startup
   through the existing disk cache (free after the first time).
5. **Run the owner decision on partials** so it is ready at end of speech.
6. **Do not chase the 250 ms number end to end.** Display it honestly:
   "Bulbul first audio: N ms" = server time from TTS request to first audio
   byte. That is the claim the demo exists to show.

### Gaps (Q2)
- Every Sarvam number here is a vendor claim. Day-one task: a 20-line probe
  that logs STT partial/final timing and TTS first-byte timing from our host
  (needs the user's approval for the spend; a few rupees).
- `sarvam-105b-conversations` TTFT with `reasoning_effort: null` unknown.
- Where Sarvam's API is hosted vs our server: unknown; host our server in
  India (Mumbai region) to be safe.

## 3. Browser audio pipeline

### Takeaway (Q3)
One `AudioContext`, two AudioWorklets: a mic worklet (downsample to 16 kHz
Int16, 20 ms frames to the server) and a player worklet (ring buffer of PCM,
resample for pitch, RMS out for the mouth, instant clear on barge-in). Make it
**half-duplex** like Talking Tom: ignore the mic while the bird or owner is
speaking. That removes the echo problem instead of solving it. Pitch-up by
plain resampling (chipmunk), not a pitch shifter.

### Findings
- **Browser VAD**: `@ricky0123/vad-web` runs Silero VAD via onnxruntime-web,
  16 kHz, callbacks `onSpeechStart` / `onSpeechEnd(Float32Array)`.
  https://github.com/ricky0123/vad. Defaults `positiveSpeechThreshold` 0.3,
  `negativeSpeechThreshold` 0.25, **`redemptionMs` 1400**, `preSpeechPadMs`
  800, `minSpeechMs` 400; frames 512 samples = 32 ms (v5).
  https://docs.vad.ricky0123.com/user-guide/algorithm/. For us,
  `redemptionMs` must drop to ~250–300 or the bird waits 1.4 s.
- **Do we need a browser VAD at all?** Sarvam's realtime STT has server VAD
  and emits `vad.speech_start` / `vad.speech_end`; Sarvam's Pipecat guide says
  use server VAD and "do not add Silero" (adds a second VAD's delay).
  https://docs.sarvam.ai/api/integration/pipecat-production-guide. Two reasons
  to still use it: (a) it lets us stop streaming silence, since STT is billed
  on `audio_duration_s` streamed; (b) endpointing control in `manual` mode.
  Recommendation: start with server VAD (`silence_duration_ms` 300) and add
  vad-web only if cost or endpoint speed demands it.
- **Echo cancellation**: Chromium does **not** apply AEC to audio played via
  the Web Audio API, only to media elements / WebRTC; Safari and Firefox do.
  Workaround is a local WebRTC loopback into an `<audio>` element.
  https://docs.atmoky.com/known-issues. Even with AEC, deployed false
  barge-in rates run 46–64% and the residual echo tail is 200–500 ms in
  typical rooms (barock.dev, iOS VPIO), fix there was an 800 ms post-playback
  mic gate. `D:\learn\speech\cs224s\experiments\exp002-barge-in\README.md`
  problem 5; `exp002-barge-in\research\e1-industry.md` (barock.dev entry).
  → **Gate the mic**: while bird/owner audio plays and for ~400 ms after,
  drop mic frames (or keep sending but ignore transcripts). The user never
  needs to interrupt the bird; the owner does that, and the owner is us.
  Still request `echoCancellation: true` for the cases where the user talks
  over the tail.
- **Gapless streamed PCM**: use an AudioWorklet with a ring buffer (FIFO);
  underflow gives silence and an audible glitch.
  https://developer.chrome.com/blog/audio-worklet-design-pattern. `ringbuf.js`
  is a lock-free SPSC buffer but needs SharedArrayBuffer and cross-origin
  isolation headers. https://github.com/br-matt/ringbuf.js. For us,
  `port.postMessage` of Float32 chunks into a JS array queue inside the worklet
  is enough (chunks arrive every tens of ms, not every 2.7 ms).
- Ask Sarvam for `linear16` (raw PCM) at 24000 Hz on the stream; no decoding
  needed in the browser, no MP3 frame boundaries.
  https://docs.sarvam.ai/api-reference/text-to-speech/stream.md
- **Pitch-up**: server `pitch` is ignored on v4-flash (same source), so do it
  client-side. `playbackRate` resamples (k-rate AudioParam), which changes
  speed and pitch together. https://developer.mozilla.org/en-US/docs/Web/API/AudioBufferSourceNode/playbackRate
  That chipmunk effect is exactly the Talking Tom sound. In the worklet, read
  the ring buffer at a fractional step (e.g. 1.35) with linear interpolation.
  Compensate speed with Sarvam `pace` (0.5–2.0 on v4-flash, docs above):
  `pace` 0.8 × resample 1.35 ≈ 1.08x speed at +5 semitones. A bonus: the
  bird's line is ~25% shorter.
- Proper pitch shifters exist if we want pitch without speed: Signalsmith
  Stretch (WASM AudioWorklet, live input, reports its own latency),
  SoundTouchJS AudioWorklet, rubberband-web (GPL-2.0).
  https://npmjs.com/package/signalsmith-stretch,
  https://github.com/cutterbl/soundtouchjs-audio-worklet,
  https://classic.yarnpkg.com/en/package/rubberband-web. No latency numbers
  published; they add buffering, which costs us TTFA. Skip for the 20-hour build.
- **Instant cut**: post `{type:"clear"}` to the player worklet; it ramps gain
  to 0 over ~5–10 ms (avoids a click) and empties the queue. Audible stop =
  that ramp + `AudioContext.outputLatency`. Track samples actually played so
  we know where the bird was cut (OpenAI Realtime's `conversation.item.truncate`
  needs `audio_end_ms` from *played* audio, clamped to received length;
  developers who used streamed length were off by seconds).
  https://community.openai.com/t/realtime-api-interruptions-dont-properly-trim-the-transcript/1000703,
  https://github.com/openai/openai-agents-python/pull/4122
- **Mouth amplitude**: compute RMS per 128-sample render quantum in the player
  worklet and post it at ~60 Hz (or put an `AnalyserNode` after the worklet
  and read `getFloatTimeDomainData` in `requestAnimationFrame`). Post the
  value *after* resampling so the mouth matches the pitched audio. (Design
  choice; the animation agent owns how it is used.)
- **Autoplay / unlock**: Web Audio playback started outside a user gesture is
  blocked; `navigator.getAutoplayPolicy("audiocontext")` reports the policy.
  https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay.
  Create the `AudioContext` and call `resume()` and `getUserMedia` inside the
  first tap ("tap the bird to wake it").
- **iOS Safari quirks**:
  - Playback quality drops (lower sample rate, mono) once `getUserMedia`
    starts, on iOS up to 26.4; open WebKit bug, macOS unaffected.
    https://bugs.webkit.org/show_bug.cgi?id=311451
  - Playback volume can drop or shift to the earpiece when capture starts.
    https://bugs.webkit.org/show_bug.cgi?id=218012,
    https://bugs.webkit.org/show_bug.cgi?id=260501
  - `navigator.audioSession.type = "play-and-record"` declares a call-like
    session; it may route to the earpiece on mobile. Experimental,
    limited availability. https://developer.mozilla.org/en-US/docs/Web/API/AudioSession
  - Practical: test on a real iPhone on day one; consider stopping the mic
    track while the bird talks (half-duplex makes this possible), which may
    restore loudspeaker playback. Unverified.
- **Mic capture**: `getUserMedia({audio:{echoCancellation:true,
  noiseSuppression:true, autoGainControl:true, channelCount:1}})`, then a
  worklet that downsamples 48k→16k and packs Int16 little-endian. Sarvam
  realtime STT accepts only 8000/16000 Hz `linear16` mono.
  https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/realtime-streaming

### Gaps (Q3)
- Whether stopping/restarting the mic track per turn on iOS fixes volume
  routing: needs a device test.
- Chrome AEC with Web Audio output: the Atmoky note says the bug is years old
  and open; current status not confirmed. Half-duplex makes it moot.

## 4. Architecture

### Takeaway (Q4)
One browser WebSocket per session to FastAPI. The server holds one Sarvam STT
socket per session and sends each transcript event down two concurrent paths:
the bird (TTS of the final, pitched in the browser) and the owner (regex on
every partial, LLM only when the regex cannot decide). Every audio chunk
carries an utterance id. Cancelling means: cancel the task, tell the browser
to clear, drop late chunks with the old id.

### Findings and design
- **Key on the server only.** Sarvam WS auth is the `Api-Subscription-Key`
  header with no query-param form, so the browser cannot connect directly
  anyway. https://docs.sarvam.ai/api-reference/text-to-speech/stream.md
  Our `sarvam.py` already keeps the key server-side.
  `D:\bulbul-build\src\bulbul_build\sarvam.py` line 41.
- **Browser ↔ server protocol** (our design):
  - binary up: 20 ms Int16 16 kHz mic frames.
  - binary down: `[1 byte voice: bird|owner][4 bytes utt_id][PCM 24 kHz Int16]`.
  - JSON both ways: `partial`, `final`, `bird_start`, `cut {utt_id}`,
    `owner_say {text}`, `metrics {stt_final_ms, tts_ttfa_ms}`, and from the
    browser `played_ms` on cut.
- **Server per session** (asyncio tasks):
  1. `mic_pump`: browser frames → Sarvam STT `audio_input` (base64). Drop
     frames while gated (bird/owner speaking + 400 ms).
  2. `stt_reader`: Sarvam events → `TurnController`.
  3. `TurnController`, a state machine: LISTENING → BIRD_SPEAKING →
     OWNER_SPEAKING → LISTENING. On each partial: run the guard pre-filter. On
     final: start `bird_task` and, if the guard is undecided, `owner_llm_task`,
     concurrently.
  4. `bird_task`: stream TTS (v4-flash, `linear16`, 24 kHz) → browser, tagged
     with utt_id. Record time to first byte for the on-screen metric.
  5. On barge-in: `bird_task.cancel()` (closes the Sarvam stream or socket,
     the only cancel Sarvam offers), send `{"type":"cut","utt_id":..}` so the
     browser clears its buffer, then play the owner line.
     https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/streaming-api/web-socket
- **TTS transport choice**: HTTP stream `POST /text-to-speech/stream` (raw
  binary, one request per utterance, cancel = close the response) through a
  warm httpx client is the simplest. The WS gives a pre-configured,
  pre-connected socket but must be reopened after every cancel (no cancel
  message). Start with HTTP stream; switch if the day-one probe shows the WS
  is clearly faster.
  https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/streaming-api/http-stream
- **STT setup**: `wss://api.sarvam.ai/speech-to-text-realtime/ws`,
  `model=saaras:v3-realtime` (also try `saaras:v4`), `language_code=auto`,
  `stream_type=fast`, `endpointing=vad`, `silence_duration_ms=300`,
  `sample_rate=16000`, `encoding=linear16`, `mode=transcribe` (native script
  is better for TTS; romanised Hindi sounds worse, per `D:\bulbul-build\CLAUDE.md`).
  Send `ping` to avoid close 1008. Rebuild on close: Pipecat notes there is no
  automatic STT reconnect and audio in flight is lost.
  https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/realtime-streaming,
  https://docs.sarvam.ai/api/integration/pipecat-production-guide
- **Fast guard: deterministic first, LLM second.**
  - OTP / phone / card: Python `re` `\d` matches all Unicode decimal digits,
    so Devanagari and other Indic digits are covered. Flag 4+ digits in a run
    (allow spaces and hyphens), or 4+ consecutive number words (Hindi एक, दो,
    तीन ... शून्य / ज़ीरो; English one, two ...; "double"), or keywords OTP,
    ओटीपी, PIN, CVV, पासवर्ड. This is our rule design. How Saaras writes
    spoken digits is unknown: test whether it gives "4 5 6 7" or words.
  - Abuse: word-list match on the normalised transcript, Devanagari and roman
    forms. Seed lists: censor-text Hindi list (archived 2024)
    https://github.com/censor-text/profanity-list; TextDetox multilingual toxic
    lexicon (has Hindi) https://hf.co/datasets/textdetox/multilingual_toxic_lexicon;
    the 209-word Hinglish profanity dictionary in Mathur et al. 2018
    https://arxiv.org/pdf/1809.08652 (public release not confirmed).
  - Other language: `language` on `transcript.partial` / `final` (with
    `language_code=auto`) differs from the bird's language and
    `language_confidence` is high.
    https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/realtime-streaming
  - Question: cheap hints (`?`, क्या, क्यों, कैसे, कब, कहाँ, कौन, what, why,
    how) → the LLM confirms and writes the owner's one-liner.
  - LLM call: `sarvam-105b-conversations`, `reasoning_effort: null`,
    `max_tokens` about 80, strict `json_schema`, schema
    `{action: none|question|abuse|other_language, reply: str}`.
    https://docs.sarvam.ai/api/api-guides-tutorials/chat-completion/overview
- **Truncate, do not race, for the sensitive cases.** When the regex fires we
  already know where the digits or the abusive word start. Send the bird only
  the text before that point ("मेरा OTP है"), then cut and play the owner.
  The bird can never say the digits or the word, and the cut still lands
  mid-sentence. Use the race (bird plays, owner cuts in later) only for the
  LLM cases (question, other language), where nothing harmful is repeated.
- **Cost control with the ledger** (`D:\bulbul-build\src\bulbul_build\budget.py`):
  - STT: reserve per turn (for example 30 s of audio at the ledger's `stt`
    price), settle from `session.end.audio_duration_s` (billed audio, server
    side). Or reserve per-minute slices while the socket is open.
  - TTS: reserve chars before the stream. On cancel, settle the full chars;
    billing for a closed stream is not documented.
  - LLM: as `chat_json` today, with the small `max_tokens`.
  - If the regex decides, no LLM call is made.
  - Rough cost per turn at ledger prices: 3 s STT about Rs 0.025, 40 chars of
    bird TTS about Rs 0.08, 60-char owner line about Rs 0.12, LLM about
    Rs 0.01. So **about Rs 0.1–0.25 per turn**. The ledger's STT price
    (Rs 29.40/h, `budget.py` line 29) differs from the marketing page's
    "Rs. 1.5 per minute" (Rs 90/h), https://www.sarvam.ai/speech-to-text.
    Check which is current.
  - Capacity: Starter allows 20 concurrent STT sockets and 40 req/min on the
    105b models. https://docs.sarvam.ai/api/getting-started/ratelimits.
    Close the STT socket when the tab is hidden or after 30 s idle.

### Gaps (Q4)
- Whether `transcript.partial` carries `language` early enough to decide
  before the user stops. Docs say it is added "when auto"; timing unknown.
- How Saaras writes spoken digits (numerals or words) in Hindi.

## 5. Known patterns to copy

### Takeaway (Q5)
Copy three things. Pipecat: an interruption cancels every stage and drains
the output queue. OpenAI Realtime: remember only what was actually played.
Vapi / ElevenLabs: use word lists where a list will do. Run guardrails in
parallel with generation and trip them, as the OpenAI Agents SDK does.

### Findings
- **Pipecat**: an `InterruptionFrame` is a system frame handled at once.
  Every processor cancels its task and drops queued frames; the LLM
  completion is aborted; TTS clears its text and drops pending output; the
  output transport drains unplayed audio; only played audio goes into the
  context. https://docs.pipecat.ai/pipecat/fundamentals/interruptions.
  VAD defaults `start_secs` 0.2, `stop_secs` 0.2, `confidence` 0.7, plus
  `MinWordsInterruptionStrategy`.
  `D:\learn\speech\cs224s\experiments\exp002-barge-in\research\e1-industry.md` §2.4.
  Copy: one `cancel_turn(utt_id)` that cancels bird TTS and LLM and tells the
  browser to clear.
- **Sarvam with Pipecat**: barge-in fires on `vad.speech_start` by default;
  gate with 3 minimum words to ignore "haan" / "achha".
  https://docs.sarvam.ai/api/integration/pipecat-production-guide
- **LiveKit**: `resume_false_interruption=True`, `false_interruption_timeout`
  2.0 s: pause, then resume if the interruption was false. An adaptive model
  separates backchannels from barge-ins (Cloud only). `e1-industry.md` §1.
  Not needed here: our interruptions are decided by us, not by the user.
- **Vapi**: `stopSpeakingPlan.numWords` 0, `voiceSeconds` 0.2,
  `backoffSeconds` 1; `startSpeakingPlan.waitSeconds` 0.4. **Retell**:
  `interruption_sensitivity` 0–1. **ElevenLabs**: `interruption_ignore_terms`
  word list. `e1-industry.md` §4, citing
  https://docs.vapi.ai/customization/speech-configuration. Word-list gates are
  normal practice in shipped products.
- **OpenAI Realtime**: `conversation.item.truncate` takes `audio_end_ms` =
  audio actually played, clamped to what was received. The server generates
  faster than real time, so the streamed length is wrong by seconds.
  https://community.openai.com/t/realtime-api-interruptions-dont-properly-trim-the-transcript/1000703,
  https://github.com/openai/openai-agents-python/pull/4122.
  Copy: the browser reports `played_ms` on cut; use it for the on-screen
  "the bird got as far as ..." text.
- **OpenAI Agents SDK guardrails**: input guardrails run "concurrently with
  the agent's execution" by default; a tripwire raises and halts the run; a
  blocking mode avoids wasted tokens.
  https://openai.github.io/openai-agents-python/guardrails/.
  Same shape as bird and owner in parallel: blocking form for OTP/abuse
  (truncate before speaking), parallel form for questions.
- **Stop speed is a separate claim from decision quality**, and vendors blur
  them (Rime: 120 ms on-prem, ~200 ms cloud stop). `e1-industry.md` §3.3.

### Gaps (Q5)
- None of these frameworks publishes a Sarvam v4-flash measurement we can reuse.

## Recommended architecture for a 20-hour build

```
Browser (one AudioContext, opened on first tap)
  mic -> [mic worklet 48k->16k Int16, 20 ms] -> WS      (dropped while bird/owner talk, +400 ms)
  WS  -> [player worklet: queue per utt_id, resample x1.35, RMS -> mouth, clear on "cut"] -> speaker

FastAPI /ws/bulbul (one per session)
  mic_pump   -> Sarvam STT realtime WS (saaras:v3-realtime, language auto, server VAD 300 ms)
  stt_reader -> TurnController
     on partial: guard.regex(text, language); remember the span if it hits
     on final:
       regex hit (OTP / abuse) -> bird TTS(text before span) -> cut -> owner (cached interjection + line)
       else bird_task: TTS stream v4-flash linear16 24 kHz -> browser   (show TTFA ms on screen)
       in parallel, if hints say question / other language:
         LLM sarvam-105b-conversations (reasoning off, json) -> act?
           yes -> bird_task.cancel() + "cut" -> cached owner interjection -> owner TTS(reply)
  every paid call: ledger.reserve -> call -> settle
```

### Latency budget (targets; measure on day one)

| Path | Step | Target |
|---|---|---|
| Bird | endpoint (server VAD 300 ms) | 300 ms |
| Bird | STT final after endpoint | 150 ms |
| Bird | Bulbul time to first audio (shown on screen) | 250 ms |
| Bird | network both legs + browser buffer | 100 ms |
| **Bird** | **end of speech → first bird audio** | **~800 ms; ~550 ms with speculative TTS on the last partial** |
| Owner (regex) | decision | before end of speech, 0 ms extra |
| Owner (LLM) | end of speech → decision | ~600–1,200 ms (unmeasured) |
| Owner | decision → first owner audio | ~30 ms (cached interjection) |
| Cut | "cut" sent → bird silent | ~20–60 ms (worklet fade + output latency) |

### Top 5 risks
1. **Vendor latency numbers are unverified.** If STT final or v4-flash TTFA
   are double the claims, the bird feels slow. Probe on day one (a small,
   approved spend) before building the UI.
2. **iOS Safari audio.** Playback degrades or moves to the earpiece once the
   mic is open (open WebKit bugs). Test on a real iPhone early; stopping the
   mic while the bird talks is the fallback.
3. **Endpointing vs Hinglish pauses.** 300 ms of silence cuts people
   mid-thought; 500 ms makes the bird feel late. Make it a live slider
   (`config.update` applies it immediately).
4. **LLM-gated owner decisions are slow and rate-limited** (105b: 40 req/min
   on Starter; TTFT unknown). Let the regex and word lists do most of the
   work; use the LLM only for questions and unclear cases.
5. **Cancellation leaks.** No TTS cancel message, late chunks after a cut,
   unknown billing for closed streams. Tag every chunk with utt_id, drop stale
   chunks in the browser, reserve the full cost.

## Measured on live APIs (2026-10-14 22:35 IST, `scripts/probe_latency.py`)

From this dev machine to api.sarvam.ai. Input: 6 cached v4-flash clips
streamed at real-time pace; speech end found by an energy threshold.

| Step | Result |
|---|---|
| STT `saaras:v3-realtime`, fast, `silence_duration_ms=300`: speech end → `vad.speech_end` | 468–582 ms (one 1021 ms outlier on the first clip) |
| STT speech end → `transcript.final` | 601–710 ms (1082 ms outlier); language auto-detect was right on all 6 |
| LLM `sarvam-105b-conversations`, `reasoning_effort: null`, streamed, ~30 output tokens | first token 112–299 ms, done 151–363 ms |
| TTS v4-flash WebSocket, flush → first audio | 317–319 ms (2 runs) |
| TTS WebSocket connect | 1626 ms cold, 288 ms warm: keep a socket open |
| TTS HTTP stream | not measured: daily cap reached |

Uncle path, end of speech → uncle's first audio: ~650 (STT final) + ~200
(LLM) + ~320 (TTS) ≈ **1.2 s**. A cached filler line can play at ~0.85 s.
The LLM stepped in on all 4 test inputs: the prompt needs to make it rarer.

Second run (TTS only, 5 lines each, same evening): WebSocket flush → first
audio 302–340 ms (median 317), connect 250–361 ms. HTTP stream
(`/text-to-speech/stream`, linear16, warm connection) first byte median
275 ms (244 min), with one 4066 ms outlier. Use the WebSocket with a
pre-opened socket; HTTP stream as the fallback.
