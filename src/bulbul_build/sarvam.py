"""Thin async client for the Sarvam APIs this repo uses.

Every paid call goes through the ledger: reserve a worst-case cost first,
settle with actual units after. The API key stays here, on the server.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import TypeVar

import httpx
from pydantic import BaseModel

from .budget import Ledger, cost_of, llm_cost

BASE = "https://api.sarvam.ai"
TTS_MODEL = "bulbul:v4-flash"
LLM_MODEL = "sarvam-105b"
TTS_MAX_CHARS = 2500

T = TypeVar("T", bound=BaseModel)


class SarvamError(RuntimeError):
    pass


class Sarvam:
    def __init__(self, api_key: str, ledger: Ledger, cache_dir: Path, client: httpx.AsyncClient | None = None):
        if not api_key:
            raise SarvamError("SARVAM_API_KEY is not set")
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
    ) -> T:
        """Ask sarvam-105b for JSON matching `schema` and validate it."""
        body = {
            "model": LLM_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "reasoning_effort": "low",
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
        content = data["choices"][0]["message"].get("content") or ""
        content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return schema.model_validate_json(content)
        except ValueError as e:
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
