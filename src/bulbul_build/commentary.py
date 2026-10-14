"""Gully Bhaiya: live Hinglish commentary for the cricket game, one line per event.

Browser -> server
  {"type": "event", "id", "kind", "state", "player", "detail"}
      kind: "start" | "ball" | "hit" | "miss" | "wicket" | "over" | "end"
      state: runs, wickets, balls_left, target, bowler, pitch
      player: swings, early_ms_avg (positive = early), late_count, early_count,
              sixes, fours, dots

Server -> browser
  {"type": "line", "id", "text"}          then PCM: 4-byte little-endian id + 24 kHz int16
  {"type": "line_end", "id", "llm_ms", "ttfa_ms"}
  {"type": "skip", "id"}                  a newer event made this one stale

The point is speed: the line is asked for the moment the bat meets the ball,
so with the LLM at ~200 ms and Bulbul's first audio at ~300 ms it lands while
the ball is still in the air. A newer event cancels an older line that has
not started speaking.
"""

from __future__ import annotations

import asyncio
import json
import logging
import struct
import time

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .budget import BudgetExceeded
from .modes.base import script_share
from .sarvam import Sarvam, SarvamError

log = logging.getLogger("bulbul.cricket")

MODE = "gully-cricket"
MAX_EVENTS = 120  # per connection; a 2-over match is ~30
VOICE = ("ratan_hi_sports", "hi-IN")
PACE = 1.1

SYSTEM = """You are "Gully Bhaiya", a loud, funny gully-cricket commentator from a Delhi or
Mumbai lane, commentating live on one player batting in a phone game. Hinglish, energetic,
short. React to THIS event using the score and the player's habits. Tease them when they
miss, hype them on big hits, and give a practical tip when asked for one. Use desi cricket
flavour (gully rules, "ek tip ek haath", the aunty's window, chai break) now and then.
Never repeat a line you already said below.

Write Hindi words in Devanagari and English words in Latin. Numbers as digits.
Return JSON: {"line": "..."} with at most WORDS words.
"""

KIND_HINT = {
    "start": "The match is starting: set the scene (target, balls, bowler, pitch) in one breath.",
    "ball": "The bowler is running in: a quick build-up line.",
    "hit": "The batter just hit the ball: call the shot and the runs.",
    "miss": "The batter missed or did not swing and the ball went past.",
    "wicket": "The batter is OUT: dramatic.",
    "over": "End of the over: give ONE specific coaching tip from the player's timing stats.",
    "end": "Match over: the verdict, win or lose, with a cheeky line to make them play again.",
}
WORDS = {"over": 22, "end": 22, "start": 20}


class Line(BaseModel):
    line: str = Field(max_length=300)


def prompt(event: dict, said: list[str]) -> str:
    kind = event.get("kind", "hit")
    parts = [
        f"Event: {KIND_HINT.get(kind, kind)}",
        f"Detail: {json.dumps(event.get('detail') or {}, ensure_ascii=False)}",
        f"Score: {json.dumps(event.get('state') or {}, ensure_ascii=False)}",
        f"Player habits: {json.dumps(event.get('player') or {}, ensure_ascii=False)}",
    ]
    if said:
        parts.append("Already said: " + " | ".join(said[-6:]))
    return "\n".join(parts)


def line_ok(text: str) -> bool:
    return bool(text.strip()) and script_share(text, "hi") >= 0.25


FALLBACK = {
    "start": "चलो भाई, match शुरू! आज तो धुलाई होगी!",
    "ball": "Bowler दौड़ा…",
    "hit": "क्या shot मारा है!",
    "miss": "अरे, निकल गई बॉल!",
    "wicket": "OUT! गया भाई गया!",
    "over": "Bat थोड़ा देर से घुमाओ, बॉल को आने दो।",
    "end": "Match खत्म! एक और हो जाए?",
}


class Commentary:
    def __init__(self, ws: WebSocket, sarvam: Sarvam):
        self.ws = ws
        self.sarvam = sarvam
        self.send_lock = asyncio.Lock()
        self.current: asyncio.Task | None = None
        self.current_id = -1
        self.speaking = False
        self.said: list[str] = []
        self.events = 0

    async def send(self, msg: dict) -> None:
        async with self.send_lock:
            await self.ws.send_text(json.dumps(msg, ensure_ascii=False))

    async def run(self) -> None:
        try:
            while True:
                data = json.loads(await self.ws.receive_text())
                if data.get("type") != "event":
                    continue
                self.events += 1
                if self.events > MAX_EVENTS:
                    continue
                await self.on_event(data)
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            if self.current and not self.current.done():
                self.current.cancel()

    async def on_event(self, event: dict) -> None:
        # A newer event makes an unspoken line stale; a line already speaking finishes,
        # except that a wicket or the end of the match always takes over.
        urgent = event.get("kind") in ("wicket", "end", "over")
        if self.current and not self.current.done() and (not self.speaking or urgent):
            self.current.cancel()
            await self.send({"type": "skip", "id": self.current_id})
        elif self.current and not self.current.done():
            return  # mid-sentence; let it finish rather than talk over it
        self.current_id = int(event.get("id", 0))
        self.current = asyncio.create_task(self.speak(self.current_id, event))

    async def speak(self, eid: int, event: dict) -> None:
        kind = event.get("kind", "hit")
        t0 = time.perf_counter()
        try:
            reply = await self.sarvam.chat_json(
                SYSTEM.replace("WORDS", str(WORDS.get(kind, 12))), prompt(event, self.said), Line,
                mode=MODE, max_tokens=120, temperature=0.95, reasoning=None,
            )
            text = reply.line.strip()
        except SarvamError as e:
            log.warning("commentary LLM failed: %s", e)
            text = ""
        except BudgetExceeded:
            await self.send({"type": "error", "message": "Aaj ka quota khatam!"})
            return
        if not line_ok(text):
            text = FALLBACK.get(kind, FALLBACK["hit"])
        llm_ms = round((time.perf_counter() - t0) * 1000)
        self.said.append(text)
        await self.send({"type": "line", "id": eid, "text": text, "kind": kind})
        t1 = time.perf_counter()
        ttfa = None
        rest = b""
        try:
            self.speaking = True
            async for chunk in self.sarvam.tts_stream(text, VOICE[1], VOICE[0], mode=MODE, pace=PACE):
                if ttfa is None:
                    ttfa = round((time.perf_counter() - t1) * 1000)
                chunk = rest + chunk
                cut = len(chunk) - len(chunk) % 2
                rest = chunk[cut:]
                if cut:
                    async with self.send_lock:
                        await self.ws.send_bytes(struct.pack("<I", eid) + chunk[:cut])
        except BudgetExceeded:
            await self.send({"type": "error", "message": "Aaj ka quota khatam!"})
            return
        except SarvamError as e:
            log.warning("commentary TTS failed: %s", e)
        finally:
            self.speaking = False
        await self.send({"type": "line_end", "id": eid, "llm_ms": llm_ms, "ttfa_ms": ttfa})
