"""Thin async client for the Sarvam APIs this repo uses.

Every paid call goes through the ledger: reserve a worst-case cost first,
settle with actual units after. The API key stays here, on the server.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from contextlib import asynccontextmanager
from urllib.parse import urlencode
from pathlib import Path
from typing import AsyncIterator, TypeVar

import httpx
import websockets
from pydantic import BaseModel

from .budget import Ledger, cost_of, llm_cost

BASE = "https://api.sarvam.ai"
TTS_MODEL = "bulbul:v4-flash"
# sarvam-105b spends its whole budget on hidden reasoning and returns no content
# for these short jobs (probed 2026-10-14: 899 of 900 tokens were reasoning).
# The conversations variant answers directly.
LLM_MODEL = "sarvam-105b-conversations"
TTS_MAX_CHARS = 2500
TTS_STREAM_RATE = 24000
# saaras:v4 takes keyterms (names to bias towards); v3-realtime does not.
# Override with STT_MODEL=saaras:v3-realtime to compare.
STT_MODEL = os.environ.get("STT_MODEL", "saaras:v4")
# Realtime STT is priced at Rs 1.5/min on sarvam.ai/speech-to-text, above the
# batch price in budget.PRICES; reserve at the higher one.
STT_REALTIME_INR_PER_S = 1.5 / 60

T = TypeVar("T", bound=BaseModel)
log = logging.getLogger(__name__)


class SarvamError(RuntimeError):
    pass


class RealtimeSTT:
    """One realtime STT socket. Send 16 kHz int16 PCM between `start` and `end`."""

    def __init__(self, max_seconds: float):
        self._ws = None
        self.max_seconds = max_seconds
        self.sent_seconds = 0.0

    async def start(self) -> None:
        await self._ws.send(json.dumps({"event": "speech_start"}))

    async def audio(self, pcm: bytes) -> None:
        secs = len(pcm) / 32000
        if self.sent_seconds + secs > self.max_seconds:
            raise SarvamError("realtime STT audio budget used up")
        self.sent_seconds += secs
        await self._ws.send(json.dumps({"event": "audio_input", "audio": base64.b64encode(pcm).decode()}))

    async def end(self) -> None:
        await self._ws.send(json.dumps({"event": "speech_end"}))
        await self._ws.send(json.dumps({"event": "flush"}))

    async def events(self) -> AsyncIterator[dict]:
        async for raw in self._ws:
            yield json.loads(raw)


class Sarvam:
    def __init__(self, api_key: str, ledger: Ledger, cache_dir: Path, client: httpx.AsyncClient | None = None):
        if not api_key:
            raise SarvamError("SARVAM_API_KEY is not set")
        self._key = api_key
        self._headers = {"api-subscription-key": api_key, "Authorization": f"Bearer {api_key}"}
        self.ledger = ledger
        self.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._http = client or httpx.AsyncClient(base_url=BASE, timeout=60)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _post(self, path: str, body: dict, call_id: int) -> dict:
        try:
            r = await self._http.post(path, json=body, headers=self._headers)
        except httpx.HTTPError as e:
            # Unknown whether it was billed: keep the reservation as spent.
            self.ledger.settle(call_id, self._reserved(call_id), 0, "error", type(e).__name__)
            raise SarvamError(f"network error calling {path}") from e
        if r.status_code >= 400:
            billed = self._reserved(call_id) if r.status_code >= 500 else 0.0
            self.ledger.settle(call_id, billed, 0, f"http_{r.status_code}", r.text[:200])
            raise SarvamError(f"{path} returned {r.status_code}: {r.text[:300]}")
        return r.json()

    def _reserved(self, call_id: int) -> float:
        with self.ledger._connect() as db:
            return float(db.execute("select inr from calls where id=?", (call_id,)).fetchone()[0])

    # ---- text to speech -------------------------------------------------

    async def tts(
        self,
        text: str,
        language: str,
        speaker: str,
        *,
        mode: str,
        pace: float = 1.0,
        sample_rate: int = 24000,
        dict_id: str | None = None,
    ) -> bytes:
        """Return WAV bytes. Identical requests are served from disk for free."""
        if not text.strip():
            raise SarvamError("empty text")
        if len(text) > TTS_MAX_CHARS:
            raise SarvamError(f"text is {len(text)} chars; limit is {TTS_MAX_CHARS}")
        body = {
            "text": text,
            "language_code": language,
            "model": TTS_MODEL,
            "speaker": speaker,
            "pace": pace,
            "speech_sample_rate": sample_rate,
            "output_audio_codec": "wav",
        }
        if dict_id:
            body["dict_id"] = dict_id
        key = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        cached = self.cache_dir / f"tts-{key}.wav"
        if cached.exists():
            return cached.read_bytes()
        chars = len(text)
        call_id = self.ledger.reserve("tts", mode, cost_of("tts", chars), chars)
        data = await self._post("/text-to-speech", body, call_id)
        self.ledger.settle(call_id, cost_of("tts", chars), chars, "ok")
        wav = base64.b64decode("".join(data["audios"]))
        cached.write_bytes(wav)
        return wav

    async def tts_stream(
        self, text: str, language: str, speaker: str, *, mode: str, pace: float = 1.0
    ) -> AsyncIterator[bytes]:
        """Yield raw 16-bit mono PCM at TTS_STREAM_RATE as Bulbul produces it.

        Measured 2026-10-14: first bytes ~275 ms after the request on a warm
        connection. Closing the iterator early stops the download; the whole
        text is still counted as spent, since Sarvam does not say otherwise.
        """
        if not text.strip():
            raise SarvamError("empty text")
        if len(text) > TTS_MAX_CHARS:
            raise SarvamError(f"text is {len(text)} chars; limit is {TTS_MAX_CHARS}")
        body = {
            "text": text,
            "language_code": language,
            "model": TTS_MODEL,
            "speaker": speaker,
            "pace": pace,
            "speech_sample_rate": TTS_STREAM_RATE,
            "output_audio_codec": "linear16",
        }
        chars = len(text)
        call_id = self.ledger.reserve("tts", mode, cost_of("tts", chars), chars)
        try:
            async with self._http.stream("POST", "/text-to-speech/stream", json=body, headers=self._headers) as r:
                if r.status_code >= 400:
                    err = (await r.aread()).decode(errors="replace")[:300]
                    self.ledger.settle(call_id, 0.0, 0, f"http_{r.status_code}", err)
                    raise SarvamError(f"tts stream returned {r.status_code}: {err}")
                async for chunk in r.aiter_bytes():
                    yield chunk
        except httpx.HTTPError as e:
            self.ledger.settle(call_id, self._reserved(call_id), 0, "error", type(e).__name__)
            raise SarvamError("network error in tts stream") from e
        finally:
            with self.ledger._connect() as db:
                status = db.execute("select status from calls where id=?", (call_id,)).fetchone()[0]
            if status == "reserved":
                self.ledger.settle(call_id, cost_of("tts", chars), chars, "ok")

    # ---- realtime speech to text ------------------------------------------

    @asynccontextmanager
    async def stt_realtime(
        self, *, mode: str, max_seconds: float, bias_words: list[str] | None = None, prompt: str | None = None,
        language: str = "auto",
    ) -> AsyncIterator["RealtimeSTT"]:
        """Open a realtime STT socket with manual endpointing.

        The caller marks speech start and end (from its own VAD) and only sends
        audio while someone is speaking, so silence is never billed.
        `max_seconds` of audio is reserved up front and settled on close.
        """
        call_id = self.ledger.reserve("stt", mode, max_seconds * STT_REALTIME_INR_PER_S, max_seconds)
        params = {
            "model": STT_MODEL, "language_code": language, "stream_type": "fast",
            "endpointing": "manual", "sample_rate": 16000, "encoding": "linear16",
        }
        if bias_words and STT_MODEL == "saaras:v4":  # Sarvam calls these keyterms; v4 only
            params["keyterms"] = json.dumps(bias_words, ensure_ascii=False)
        if prompt:
            params["prompt"] = prompt
        url = "wss://api.sarvam.ai/speech-to-text-realtime/ws?" + urlencode(params)
        stt = RealtimeSTT(max_seconds)
        try:
            async with websockets.connect(url, additional_headers={"api-subscription-key": self._key}) as ws:
                stt._ws = ws
                yield stt
        except (OSError, websockets.WebSocketException) as e:
            raise SarvamError(f"realtime STT failed: {type(e).__name__}") from e
        finally:
            secs = min(stt.sent_seconds, max_seconds)
            self.ledger.settle(call_id, secs * STT_REALTIME_INR_PER_S, secs, "ok")

    # ---- LLM with structured output --------------------------------------

    async def chat_json(
        self,
        system: str,
        user: str,
        schema: type[T],
        *,
        mode: str,
        max_tokens: int = 1200,
        temperature: float = 0.7,
        reasoning: str | None = "low",
    ) -> T:
        """Ask sarvam-105b for JSON matching `schema` and validate it.

        `reasoning=None` turns thinking off: measured 2026-10-14 at ~200 ms
        for a 30-token reply, which the live uncle needs.
        """
        body = {
            "model": LLM_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "reasoning_effort": reasoning,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema(), "strict": True},
            },
        }
        # Worst case: every input char is a token, output hits max_tokens.
        est_in = len(system) + len(user) + len(json.dumps(body["response_format"]))
        call_id = self.ledger.reserve("llm", mode, llm_cost(est_in, max_tokens), est_in + max_tokens)
        data = await self._post("/v1/chat/completions", body, call_id)
        usage = data.get("usage") or {}
        t_in, t_out = usage.get("prompt_tokens"), usage.get("completion_tokens")
        if t_in is None or t_out is None:
            self.ledger.settle(call_id, self._reserved(call_id), est_in + max_tokens, "ok", "no usage; kept estimate")
        else:
            self.ledger.settle(call_id, llm_cost(t_in, t_out), t_in + t_out, "ok")
        choice = data["choices"][0]
        content = choice["message"].get("content") or ""
        content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        start, end = content.find("{"), content.rfind("}")
        if start != -1 and end > start:
            content = content[start : end + 1]
        try:
            return schema.model_validate_json(content)
        except ValueError as e:
            log.warning(
                "LLM output did not match %s (finish_reason=%s, %d chars): %r",
                schema.__name__, choice.get("finish_reason"), len(content), content[:300],
            )
            raise SarvamError(f"LLM output did not match {schema.__name__}") from e

    # ---- translate --------------------------------------------------------

    async def translate(self, text: str, source: str, target: str, *, mode: str) -> str:
        chars = len(text)
        call_id = self.ledger.reserve("translate", mode, cost_of("translate", chars), chars)
        data = await self._post(
            "/translate",
            {"input": text, "source_language_code": source, "target_language_code": target},
            call_id,
        )
        self.ledger.settle(call_id, cost_of("translate", chars), chars, "ok")
        return data["translated_text"]
