"""Measure the uncle's real-time path on live Sarvam APIs. Costs money: ask first.

1. Realtime STT: stream cached clips at real-time pace, time from the end of
   speech to `vad.speech_end` and `transcript.final`.
2. LLM: the uncle's per-turn decision, streamed, time to first token and total.
3. TTS: v4-flash over WebSocket and HTTP stream, time to first audio.

Every call is reserved in the ledger first. Results go to data/probe/latency.json.
Run: uv run python scripts/probe_latency.py [--tts-only]
"""

from __future__ import annotations

import asyncio
import base64
import json
import statistics
import subprocess
import sys
import time
import wave
from pathlib import Path

import httpx
import websockets

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bulbul_build import config  # noqa: E402
from bulbul_build.budget import Caps, Ledger, cost_of, llm_cost  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "probe"
CLIPS = [  # cached v4-flash clips, 2-5 s, used as "user speech"
    "tts-0414a8cd4349a9f4231b5081792678303c8d90ac2dcefdfd291dd3865c3e7055.wav",
    "tts-0a8ee20033de88afa6f38b98340b99f58076f9da056aad175a65330be19ff333.wav",
    "tts-1020bd0673c701010c4e7f5988deb4d4c812261fce4cd9d53025e0b7942d262f.wav",
    "tts-11d1ecfb18bdbefbe43da440ee9df0118b54b8753c3f46797717fc267481839c.wav",
    "tts-17c3aa4689510abde134600f8bc3c4094e9cfc47f311c29a1412e4b2bd1da3b8.wav",
    "tts-194668fa80928ada8597dfa31616151174b79172fbfe5e7140e97fd0ed95c883.wav",
]
FRAME = 640  # 20 ms of 16 kHz mono int16
SILENCE_S = 2.0
STT_INR_PER_S = 1.5 / 60  # realtime marketing price; higher than the ledger's batch price
UNCLE_LINES = [
    "Arre beta, yeh Mitthu hai, bas repeat karta hai. Sawaal mujhse poocho.",
    "Bulbul! Chup! Sorry ji, isne galat sangat pakdi hai.",
    "OTP kisi ko nahi batate, Mitthu ko bhi nahi.",
    "Haan haan, sar pe mat chadhao isko, warna din bhar gaata rahega.",
    "Dilli se Mumbai ki flight lagbhag do ghante ki hoti hai, beta.",
]


def pcm16k(path: Path) -> bytes:
    return subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-ar", "16000", "-ac", "1", "-f", "s16le", "pipe:1"],
        capture_output=True, check=True,
    ).stdout


def speech_end_s(pcm: bytes) -> float:
    """Seconds into the clip where the last 20 ms frame above the noise floor ends."""
    import array

    a = array.array("h", pcm)
    n = len(a) // (FRAME // 2)
    last = 0
    for i in range(n):
        seg = a[i * 320:(i + 1) * 320]
        if max(abs(x) for x in seg) > 800:
            last = i + 1
    return last * 0.02


async def probe_stt(key: str, ledger: Ledger) -> list[dict]:
    clips = [pcm16k(ROOT / "data" / "cache" / c) for c in CLIPS]
    secs = sum(len(c) / 32000 + SILENCE_S for c in clips) + 1
    call_id = ledger.reserve("stt", "probe", secs * STT_INR_PER_S, secs)
    url = ("wss://api.sarvam.ai/speech-to-text-realtime/ws?language_code=auto"
           "&stream_type=fast&silence_duration_ms=300&sample_rate=16000&encoding=linear16")
    rows: list[dict] = []
    events: list[tuple[float, dict]] = []
    billed = None
    async with websockets.connect(url, additional_headers={"api-subscription-key": key}) as ws:

        async def recv():
            nonlocal billed
            async for raw in ws:
                m = json.loads(raw)
                events.append((time.perf_counter(), m))
                if m.get("event") == "session.end" or m.get("type") == "session.end":
                    billed = m.get("audio_duration_s") or (m.get("data") or {}).get("audio_duration_s")
                    return

        rt = asyncio.create_task(recv())
        silence = b"\x00" * FRAME
        t0 = time.perf_counter()
        sent = 0
        for idx, pcm in enumerate(clips):
            end_in_clip = speech_end_s(pcm)
            start_at = sent
            for off in range(0, len(pcm), FRAME) :
                await ws.send(json.dumps({"event": "audio_input", "audio": base64.b64encode(pcm[off:off + FRAME]).decode()}))
                sent += 1
                await asyncio.sleep(max(0, t0 + sent * 0.02 - time.perf_counter()))
            speech_end_wall = t0 + start_at * 0.02 + end_in_clip
            mark = len(events)
            for _ in range(int(SILENCE_S / 0.02)):
                await ws.send(json.dumps({"event": "audio_input", "audio": base64.b64encode(silence).decode()}))
                sent += 1
                await asyncio.sleep(max(0, t0 + sent * 0.02 - time.perf_counter()))
            got = {"clip": idx}
            for t, m in events[mark - 0:]:
                ev = m.get("event") or m.get("type")
                if ev in ("vad.speech_end", "transcript.final") and ev not in got and t >= speech_end_wall - 1:
                    got[ev] = round((t - speech_end_wall) * 1000)
                    if ev == "transcript.final":
                        got["text"] = m.get("text") or (m.get("data") or {}).get("text")
                        got["language"] = m.get("language") or (m.get("data") or {}).get("language")
            rows.append(got)
            print("stt", got, flush=True)
        await ws.send(json.dumps({"event": "end"}))
        try:
            await asyncio.wait_for(rt, 10)
        except asyncio.TimeoutError:
            rt.cancel()
    units = float(billed) if billed else secs
    ledger.settle(call_id, units * STT_INR_PER_S, units, "ok", f"billed_s={billed}")
    (OUT / "stt_events.json").write_text(json.dumps([m for _, m in events], ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


UNCLE_SYSTEM = (
    "You are Sharma uncle. Mitthu, your pet bulbul, sits on your palm and repeats "
    "whatever the user says. Each turn, decide if you step in. Step in for rude "
    "words, OTPs or phone numbers, real questions (answer in one line), another "
    "language (reply in it), or whenever a warm, funny uncle would. Otherwise stay "
    'quiet. Reply only with JSON: {"step_in": bool, "line": string, "language": string}. '
    "line is at most 15 words, Hinglish with Hindi words in Devanagari."
)


async def probe_llm(key: str, ledger: Ledger, texts: list[str]) -> list[dict]:
    rows = []
    async with httpx.AsyncClient(base_url="https://api.sarvam.ai", timeout=30) as http:
        for text in texts:
            body = {
                "model": "sarvam-105b-conversations",
                "messages": [{"role": "system", "content": UNCLE_SYSTEM}, {"role": "user", "content": text}],
                "max_tokens": 120, "temperature": 0.7, "reasoning_effort": None, "stream": True,
            }
            est_in = len(UNCLE_SYSTEM) + len(text)
            call_id = ledger.reserve("llm", "probe", llm_cost(est_in, 120), est_in + 120)
            t0 = time.perf_counter()
            first = None
            out = []
            usage = None
            async with http.stream("POST", "/v1/chat/completions", json=body,
                                   headers={"api-subscription-key": key, "Authorization": f"Bearer {key}"}) as r:
                if r.status_code >= 400:
                    err = (await r.aread()).decode()[:300]
                    ledger.settle(call_id, 0, 0, f"http_{r.status_code}", err)
                    rows.append({"error": r.status_code, "body": err})
                    print("llm error", r.status_code, err, flush=True)
                    continue
                async for line in r.aiter_lines():
                    if not line.startswith("data:") or line.strip() == "data: [DONE]":
                        continue
                    d = json.loads(line[5:])
                    usage = d.get("usage") or usage
                    for ch in d.get("choices") or []:
                        delta = ch.get("delta") or {}
                        piece = delta.get("content") or ""
                        if piece and first is None:
                            first = time.perf_counter()
                        out.append(piece)
            total = time.perf_counter() - t0
            t_in = (usage or {}).get("prompt_tokens", est_in)
            t_out = (usage or {}).get("completion_tokens", 120)
            ledger.settle(call_id, llm_cost(t_in, t_out), t_in + t_out, "ok")
            row = {"input": text, "ttft_ms": round((first - t0) * 1000) if first else None,
                   "total_ms": round(total * 1000), "output": "".join(out), "tokens_out": t_out}
            rows.append(row)
            print("llm", row, flush=True)
    return rows


async def probe_tts_ws(key: str, ledger: Ledger, lines: list[str]) -> list[dict]:
    rows = []
    url = "wss://api.sarvam.ai/text-to-speech/ws?model=bulbul:v4-flash&send_completion_event=true"
    for text in lines:
        call_id = ledger.reserve("tts", "probe", cost_of("tts", len(text)), len(text))
        t_conn = time.perf_counter()
        async with websockets.connect(url, additional_headers={"Api-Subscription-Key": key}) as ws:
            connected = time.perf_counter()
            await ws.send(json.dumps({"type": "config", "data": {
                "language_code": "hi-IN", "speaker": "shubh_enhi_companion",
                "speech_sample_rate": "24000", "output_audio_codec": "mp3", "min_buffer_size": 30}}))
            t0 = time.perf_counter()
            await ws.send(json.dumps({"type": "text", "data": {"text": text}}))
            await ws.send(json.dumps({"type": "flush"}))
            first = None
            nbytes = 0
            async for raw in ws:
                m = json.loads(raw)
                if m.get("type") == "audio":
                    if first is None:
                        first = time.perf_counter()
                    nbytes += len(base64.b64decode(m["data"]["audio"]))
                elif m.get("type") == "event" or m.get("type") == "error":
                    if m.get("type") == "error":
                        print("tts ws error", m, flush=True)
                    break
            done = time.perf_counter()
        ledger.settle(call_id, cost_of("tts", len(text)), len(text), "ok")
        row = {"chars": len(text), "connect_ms": round((connected - t_conn) * 1000),
               "ttfa_ms": round((first - t0) * 1000) if first else None,
               "total_ms": round((done - t0) * 1000), "bytes": nbytes}
        rows.append(row)
        print("tts_ws", row, flush=True)
    return rows


async def probe_tts_http(key: str, ledger: Ledger, lines: list[str]) -> list[dict]:
    rows = []
    async with httpx.AsyncClient(base_url="https://api.sarvam.ai", timeout=30) as http:
        await http.get("/")  # warm the TLS connection, as a server would
        for text in lines:
            call_id = ledger.reserve("tts", "probe", cost_of("tts", len(text)), len(text))
            body = {"text": text, "language_code": "hi-IN", "model": "bulbul:v4-flash",
                    "speaker": "shubh_enhi_companion", "speech_sample_rate": 24000,
                    "output_audio_codec": "linear16"}
            t0 = time.perf_counter()
            first = None
            nbytes = 0
            async with http.stream("POST", "/text-to-speech/stream", json=body,
                                   headers={"api-subscription-key": key}) as r:
                if r.status_code >= 400:
                    err = (await r.aread()).decode()[:300]
                    ledger.settle(call_id, 0, 0, f"http_{r.status_code}", err)
                    print("tts http error", r.status_code, err, flush=True)
                    rows.append({"error": r.status_code, "body": err})
                    continue
                async for chunk in r.aiter_bytes():
                    if first is None:
                        first = time.perf_counter()
                    nbytes += len(chunk)
            done = time.perf_counter()
            ledger.settle(call_id, cost_of("tts", len(text)), len(text), "ok")
            row = {"chars": len(text), "ttfa_ms": round((first - t0) * 1000) if first else None,
                   "total_ms": round((done - t0) * 1000), "audio_s": round(nbytes / 48000, 2)}
            rows.append(row)
            print("tts_http", row, flush=True)
    return rows


def summary(rows: list[dict], key: str) -> dict:
    v = [r[key] for r in rows if r.get(key) is not None]
    return {"n": len(v), "median": statistics.median(v) if v else None, "min": min(v, default=None), "max": max(v, default=None)}


async def main() -> None:
    s = config.load()
    ledger = Ledger(s.ledger_path, Caps(s.daily_budget_inr, s.total_budget_inr, s.per_call_budget_inr))
    OUT.mkdir(parents=True, exist_ok=True)
    before = ledger.spent()
    stt: list[dict] = []
    llm: list[dict] = []
    if "--tts-only" not in sys.argv:
        stt = await probe_stt(s.sarvam_api_key, ledger)
        texts = [r.get("text") or "" for r in stt if r.get("text")][:2] + [
            "Mera OTP hai 4 8 2 9 1 6", "Dilli se Mumbai kitni der ki flight hai?"]
        llm = await probe_llm(s.sarvam_api_key, ledger, texts)
    ws = await probe_tts_ws(s.sarvam_api_key, ledger, UNCLE_LINES)
    http = await probe_tts_http(s.sarvam_api_key, ledger, UNCLE_LINES)
    result = {
        "stt": stt, "llm": llm, "tts_ws": ws, "tts_http": http,
        "summary": {
            "stt_speech_end_ms": summary(stt, "vad.speech_end"),
            "stt_final_ms": summary(stt, "transcript.final"),
            "llm_ttft_ms": summary(llm, "ttft_ms"), "llm_total_ms": summary(llm, "total_ms"),
            "tts_ws_ttfa_ms": summary(ws, "ttfa_ms"), "tts_ws_connect_ms": summary(ws, "connect_ms"),
            "tts_http_ttfa_ms": summary(http, "ttfa_ms"),
        },
        "spent_inr": round(ledger.spent() - before, 3),
    }
    name = "latency_tts.json" if "--tts-only" in sys.argv else "latency.json"
    (OUT / name).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result["summary"], indent=1), "\nspent Rs", result["spent_inr"])


if __name__ == "__main__":
    asyncio.run(main())
