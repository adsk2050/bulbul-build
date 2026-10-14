"""FastAPI server: one page, one API route per mode."""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from . import audio, config
from .budget import BudgetExceeded, Caps, Ledger, cost_of
from .guard import RateLimiter
from .modes import REGISTRY, load_all
from .sarvam import Sarvam, SarvamError
from .commentary import Commentary
from .talk import Session

log = logging.getLogger("bulbul")
WEB = Path(__file__).resolve().parent / "web"
MAX_BODY = 8 * 1024
MAX_CLIP = 15 * 1024 * 1024  # a recorded share clip
TTS_CONCURRENCY = 4
GAP_MS = 250

settings = config.load()
ledger = Ledger(
    settings.ledger_path,
    Caps(settings.daily_budget_inr, settings.total_budget_inr, settings.per_call_budget_inr),
)
limiter = RateLimiter(settings.per_ip_per_min, trust_proxy=os.environ.get("TRUST_PROXY") == "1")
OUT = settings.cache_dir / "out"
UNCLE = settings.cache_dir.parent / "uncle"  # recorded fillers, scripts/make_fillers.py
MAX_TALKERS_PER_IP = 2
TALK_LOG = settings.cache_dir.parent / "talk-log.jsonl"
UTTERANCES = settings.cache_dir.parent / "utterances"
CRICKET_LOG = settings.cache_dir.parent / "cricket-log.jsonl"  # each event and the line it got  # what STT heard, for comparing STT settings  # visitor lines and replies, for tuning


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_all()
    OUT.mkdir(parents=True, exist_ok=True)
    app.state.sarvam = Sarvam(settings.sarvam_api_key, ledger, settings.cache_dir)
    yield
    await app.state.sarvam.aclose()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def security(request: Request, call_next):
    limit = MAX_CLIP if request.url.path == "/api/clip" else MAX_BODY
    if int(request.headers.get("content-length") or 0) > limit:
        return JSONResponse({"error": "request too large"}, status_code=413)
    resp = await call_next(request)
    if request.url.path in ("/talk", "/cricket") or (request.url.path.startswith("/static/") and "/art/" not in request.url.path):
        resp.headers["Cache-Control"] = "no-cache"  # always revalidate: a stale talk.js broke testing
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; script-src 'self'"
    )
    if request.url.path == "/cricket":
        # The adapted game keeps its inline script and onclick handlers.
        resp.headers["Content-Security-Policy"] = resp.headers["Content-Security-Policy"].replace(
            "script-src 'self'", "script-src 'self' 'unsafe-inline'"
        )
    return resp


@app.get("/")
@app.get("/m/{slug}")
async def page(slug: str | None = None):
    return FileResponse(WEB / "index.html")


@app.get("/cricket")
async def cricket_page():
    return FileResponse(WEB / "cricket.html")


@app.get("/talk")
async def talk_page():
    return FileResponse(WEB / "talk.html")


@app.get("/uncle/{name}")
async def uncle_clip(name: str):
    if not (name.endswith(".wav") and name[:-4].replace("-", "").isalnum()):
        raise HTTPException(404)
    path = UNCLE / name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="audio/wav", headers={"Cache-Control": "public, max-age=86400"})


_talkers: dict[str, int] = {}


@app.websocket("/ws/talk")
async def talk_ws(ws: WebSocket):
    ip = limiter.client_ip(ws)
    if _talkers.get(ip, 0) >= MAX_TALKERS_PER_IP or not limiter.allow(ip):
        await ws.close(code=1013)
        return
    await ws.accept()
    _talkers[ip] = _talkers.get(ip, 0) + 1
    try:
        await Session(ws, ws.app.state.sarvam, UNCLE, log_path=TALK_LOG, utterance_dir=UTTERANCES).run()
    finally:
        _talkers[ip] -= 1


@app.websocket("/ws/cricket")
async def cricket_ws(ws: WebSocket):
    ip = limiter.client_ip(ws)
    if _talkers.get(ip, 0) >= MAX_TALKERS_PER_IP or not limiter.allow(ip):
        await ws.close(code=1013)
        return
    await ws.accept()
    _talkers[ip] = _talkers.get(ip, 0) + 1
    try:
        await Commentary(ws, ws.app.state.sarvam, log_path=CRICKET_LOG).run()
    finally:
        _talkers[ip] -= 1


app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/api/modes")
async def modes():
    return [
        {"slug": m.slug, "name": m.name, "tagline": m.tagline, "schema": m.form.model_json_schema()}
        for m in REGISTRY.values()
    ]


@app.get("/api/budget")
async def budget(request: Request):
    if limiter.client_ip(request) not in {"127.0.0.1", "::1"}:
        raise HTTPException(404)
    return {
        "spent_today_inr": round(ledger.spent(ledger._today()), 4),
        "spent_total_inr": round(ledger.spent(), 4),
        "caps": vars(ledger.caps),
        "rows": ledger.report(),
    }


@app.post("/api/clip")
async def make_clip(request: Request):
    """Turn the browser's recording of one exchange into a shareable MP4."""
    if not limiter.allow(limiter.client_ip(request)):
        raise HTTPException(429, "Thoda ruko! Too many requests, try again in a minute.")
    kind = request.headers.get("content-type", "")
    suffix = ".mp4" if "mp4" in kind else ".webm" if "webm" in kind else None
    if suffix is None:
        raise HTTPException(415, "send video/webm or video/mp4")
    body = await request.body()
    if not body or len(body) > MAX_CLIP:
        raise HTTPException(413, "clip too large")
    try:
        mp4 = await asyncio.to_thread(audio.share_mp4, body, suffix)
    except Exception as e:  # ffmpeg failed on a bad upload
        log.warning("clip conversion failed: %s", e)
        raise HTTPException(422, "Could not make the video.") from e
    token = secrets.token_hex(12)
    (OUT / f"{token}.mp4").write_bytes(mp4)
    return {"url": f"/clip/{token}.mp4"}


@app.get("/clip/{name}")
async def clip_file(name: str):
    if not (name.endswith(".mp4") and name[:-4].isalnum()):
        raise HTTPException(404)
    path = OUT / name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="video/mp4", filename="talking-bulbul.mp4")


@app.get("/audio/{name}")
async def audio_file(name: str):
    if not (name.endswith(".wav") and name[:-4].isalnum()):
        raise HTTPException(404)
    path = OUT / name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="audio/wav")


@app.post("/api/{slug}")
async def generate(slug: str, request: Request):
    mode = REGISTRY.get(slug)
    if mode is None:
        raise HTTPException(404, "unknown mode")
    if not limiter.allow(limiter.client_ip(request)):
        raise HTTPException(429, "Thoda ruko! Too many requests, try again in a minute.")
    try:
        form = mode.form.model_validate(await request.json())
    except (ValidationError, ValueError) as e:
        raise HTTPException(422, "Please check the form fields.") from e

    sarvam: Sarvam = request.app.state.sarvam
    try:
        script = await mode.build(form, sarvam)
        # Refuse up front rather than pay for half a script.
        ledger.check_headroom(cost_of("tts", sum(len(line.text) for line in script.lines)))
        sem = asyncio.Semaphore(TTS_CONCURRENCY)

        async def synth(line):
            async with sem:
                return await sarvam.tts(line.text, line.language, line.speaker, mode=slug, pace=line.pace)

        clips = await asyncio.gather(*(synth(line) for line in script.lines))
    except BudgetExceeded as e:
        log.warning("budget stop: %s", e)
        raise HTTPException(503, "Aaj ka quota khatam! Today's free limit is used up. Try tomorrow.") from e
    except SarvamError as e:
        log.error("sarvam error in %s: %s", slug, e)
        raise HTTPException(502, "The voice service had a problem. Please try again.") from e

    wav = audio.concat_wavs(clips, gap_ms=GAP_MS)
    token = secrets.token_hex(12)
    (OUT / f"{token}.wav").write_bytes(wav)
    captions, t = [], 0.0
    for line, clip in zip(script.lines, clips):
        d = audio.duration(clip)
        captions.append({"text": line.caption or line.text, "language": line.language, "start": round(t, 3), "end": round(t + d, 3)})
        t += d + GAP_MS / 1000
    result = {
        "title": script.title,
        "share_text": script.share_text,
        "card": script.card,
        "captions": captions,
        "audio_url": f"/audio/{token}.wav",
    }
    if script.phone_line:
        (OUT / f"{token}p.wav").write_bytes(audio.phone_line(wav))
        result["phone_audio_url"] = f"/audio/{token}p.wav"
    return result


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run("bulbul_build.app:app", host="127.0.0.1", port=settings.port)
