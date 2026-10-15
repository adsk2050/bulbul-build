"""Bulbul: live Hinglish commentary for the cricket game, one line per event.

Browser -> server
  {"type": "event", "id", "game", "kind", "state", "player", "detail"}
      game: which game is being played; its rules and controls are loaded from
            cricket_rules/<game>.md and given to the commentator, so it knows
            what each key, shot and result means.
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
import random
import re
import struct
import time
from pathlib import Path

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

RULES_DIR = Path(__file__).resolve().parent / "cricket_rules"


def game_rules(game: str) -> str:
    """The rules and controls of `game`, for the commentator. Unknown games get none."""
    if not re.fullmatch(r"[a-z0-9-]{1,32}", game or ""):
        return ""
    path = RULES_DIR / f"{game}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


SYSTEM = """You are "Bulbul", a loud, funny gully-cricket commentator from a Delhi or
Mumbai lane, commentating live on one player batting in a phone game. Hinglish, energetic,
short. React to THIS event using the score and the player's habits. Tease them when they
miss, hype them on big hits, and give a practical tip when asked for one. Use desi cricket
flavour (gully rules, "ek tip ek haath", the aunty's window, chai break) now and then.
You are a character, not an analyst: react like a friend watching from the gully wall,
with shock, laughter, mock despair or wild celebration. A ball line carries at most one
fact from the data and no advice; tips belong to the end-of-over line, or to a ball
where the same mistake has now happened twice in a row.
Never repeat a line, a joke or an opening word you already used below; vary the rhythm.
Only describe what the event data says happened; never invent a shot, fielder or result.
Never say milliseconds or a timing number; say it in words ("थोड़ा जल्दी", "बहुत जल्दी",
"एकदम late", "perfect timing").
When the score data has the player's name you may use it once in that line, no more.
Otherwise say "भाई", "हीरो", "batsman" or nothing.

Write Hindi words in Devanagari and English words in Latin. Numbers as digits.
Return JSON: {"line": "..."} with at most WORDS words.
"""

KIND_HINT = {
    "start": "The match is starting. If detail.history shows past matches, give ONE specific tip "
             "from them (their usual mistake: timing, the ball that gets them out, the wrong shot) "
             "and the number to beat; for a first match, welcome them and set the scene in one breath.",
    "ball": "The bowler is running in: a quick build-up line.",
    "hit": "The batter just hit the ball: call the shot and the runs. If detail.in_air is true the ball is still in the air: build the suspense and give the result last.",
    "miss": "The batter missed or did not swing and the ball went past.",
    "wicket": "The batter is OUT: dramatic. If detail.in_air is true the catch has not landed yet: build up, reveal the OUT at the end.",
    "over": "End of the over: give ONE specific coaching tip from the player's timing stats.",
    "end": "Match over: call the last ball (detail.last_ball) and the verdict, win or lose, with a cheeky line to make them play again.",
}
WORDS = {"over": 22, "end": 22, "start": 26}
NAME_GAP = 3  # lines that must pass before the name is used again


# A different angle each line, so the commentary does not settle into one pattern.
ANGLES = [
    "a number from the score or the player's stats",
    "a gentle tease of the batter",
    "a desi comparison (chai, auto, aunty, shaadi, traffic, exams)",
    "pure hype and noise",
    "the bowler's point of view",
    "the imaginary gully crowd's reaction",
]


class Line(BaseModel):
    line: str = Field(max_length=300)


def batter_name(event: dict) -> str:
    return str((event.get("state") or {}).get("batter") or "").strip()


def name_allowed(name: str, said: list[str]) -> bool:
    """The name may go in this line: none of the last NAME_GAP lines used it."""
    return bool(name) and not any(name.lower() in s.lower() for s in said[-NAME_GAP:])


def _name_re(name: str) -> re.Pattern:
    return re.compile(rf"(?<!\w){re.escape(name)}(?!\w)", re.IGNORECASE)


def limit_name(text: str, name: str, allowed: bool) -> str:
    """At most one use of the name, and none when it is not allowed.

    An extra name used as a call-out ("Anmol, ...") is dropped; any other becomes
    भाई, or "batsman" when the line already says भाई.
    """
    if not name:
        return text
    pattern = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)(\s*,\s*)?", re.IGNORECASE)
    kept = False

    def swap(m: re.Match) -> str:
        nonlocal kept
        if allowed and not kept:
            kept = True
            return m.group(0)
        if m.group(1):
            return ""
        return "batsman" if re.search(r"भाई|bhai", text, re.IGNORECASE) else "भाई"

    out = pattern.sub(swap, text).strip()
    return out[:1].upper() + out[1:] if out else out


def prompt(event: dict, said: list[str]) -> str:
    kind = event.get("kind", "hit")
    state = dict(event.get("state") or {})
    # The model put the player's name in nearly every line (17 of 18 in one match).
    # It only sees the name when none of the last few lines used it, and then not
    # even in its own past lines, which it copied the name from.
    name = batter_name(event)
    history = said[-6:]
    if name and not name_allowed(name, said):
        state.pop("batter")
        history = [_name_re(name).sub("भाई", s) for s in history]
    parts = [
        f"Event: {KIND_HINT.get(kind, kind)}",
        f"Detail: {json.dumps(event.get('detail') or {}, ensure_ascii=False)}",
        f"Score: {json.dumps(state, ensure_ascii=False)}",
        f"Player habits: {json.dumps(event.get('player') or {}, ensure_ascii=False)}",
    ]
    if history:
        parts.append("Already said: " + " | ".join(history))
    return "\n".join(parts)


def line_ok(text: str) -> bool:
    # Hinglish needs some Devanagari; all-Latin output is usually romanised Hindi,
    # which Bulbul reads badly. The bar is low so cricket English ("cover drive") fits.
    return bool(text.strip()) and script_share(text, "hi") >= 0.15


# Used only when the LLM fails or writes the wrong script; several per event so
# the fallback does not repeat (it did, and sounded robotic).
FALLBACK = {
    "start": ["चलो भाई, match शुरू! आज तो धुलाई होगी!", "Gully stadium full है, बल्लेबाज़ तैयार!", "Target सामने है, अब दिखाओ दम!"],
    "ball": ["Bowler दौड़ा…", "ये आई बॉल…"],
    "hit": ["क्या shot मारा है!", "बल्ले से निकली गोली!", "Runs आ गए भाई!", "ये हुई ना बात!"],
    "miss": ["अरे, निकल गई बॉल!", "हवा में बल्ला घुमा दिया!", "बॉल ने चकमा दे दिया!"],
    "wicket": ["OUT! गया भाई गया!", "विकेट! Gully में सन्नाटा!", "पवेलियन का रास्ता नापो!"],
    "over": ["Bat थोड़ा देर से घुमाओ, बॉल को आने दो।", "बॉल की line देखो, फिर मारो।"],
    "end": ["Match खत्म! एक और हो जाए?", "बस इतना ही? फिर से खेलो!"],
}


class Commentary:
    def __init__(self, ws: WebSocket, sarvam: Sarvam, log_path: Path | None = None, rng: random.Random | None = None):
        self.ws = ws
        self.log_path = log_path
        self.rng = rng or random.Random()
        self.session = f"{self.rng.getrandbits(32):08x}"
        self.ended = False  # the end-of-match line is never cancelled
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

    def log(self, entry: dict) -> None:
        if self.log_path:
            entry = {"ts": round(time.time(), 1), "session": self.session, **entry}
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

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
        if event.get("kind") == "start":
            self.ended = False
        elif self.ended:
            return  # the match is over and its last line is playing
        if event.get("kind") == "end":
            self.ended = True
        # A newer event makes an unspoken line stale; a line already speaking finishes,
        # except that a wicket or the end of the match always takes over.
        # "over" waits for the current sentence; it used to cut it off mid-word.
        urgent = event.get("kind") in ("wicket", "end")
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
        system = SYSTEM.replace("WORDS", str(WORDS.get(kind, 12)))
        system += "\nThis time, angle: " + self.rng.choice(ANGLES) + "."
        rules = game_rules(str(event.get("game") or ""))
        if rules:
            system += "\nThe game being played (rules, controls, what the event fields mean):\n" + rules
        try:
            reply = await self.sarvam.chat_json(
                system, prompt(event, self.said), Line,
                mode=MODE, max_tokens=120, temperature=1.0, reasoning=None,
            )
            name = batter_name(event)
            text = limit_name(reply.line.strip(), name, name_allowed(name, self.said))
        except SarvamError as e:
            log.warning("commentary LLM failed: %s", e)
            text = ""
        except BudgetExceeded:
            await self.send({"type": "error", "message": "Aaj ka quota khatam!"})
            return
        # Romanised Hinglish is still spoken (Bulbul reads it less well, but one fixed
        # line every hit sounded worse); only an empty line falls back.
        fallback = not text.strip()
        if fallback:
            options = [t for t in FALLBACK.get(kind, FALLBACK["hit"]) if t not in self.said[-4:]]
            text = random.choice(options or FALLBACK.get(kind, FALLBACK["hit"]))
        llm_ms = round((time.perf_counter() - t0) * 1000)
        self.log({"event": {k: event.get(k) for k in ("game", "kind", "detail", "state", "player")},
                  "line": text, "fallback": fallback, "llm_ms": llm_ms})
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
