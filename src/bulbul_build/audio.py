"""Join WAV clips and make the phone-line version, with ffmpeg."""

from __future__ import annotations

import io
import shutil
import subprocess
import wave


def duration(clip: bytes) -> float:
    with wave.open(io.BytesIO(clip)) as w:
        return w.getnframes() / w.getframerate()


def concat_wavs(clips: list[bytes], gap_ms: int = 250) -> bytes:
    """Join WAV clips with a short silence between them. All clips must share a format."""
    if not clips:
        raise ValueError("no clips")
    params = None
    frames: list[bytes] = []
    for clip in clips:
        with wave.open(io.BytesIO(clip)) as w:
            p = (w.getnchannels(), w.getsampwidth(), w.getframerate())
            if params is None:
                params = p
            elif p != params:
                raise ValueError(f"clip format {p} differs from {params}")
            frames.append(w.readframes(w.getnframes()))
    ch, width, rate = params
    silence = b"\x00" * (int(rate * gap_ms / 1000) * ch * width)
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(silence.join(frames))
    return out.getvalue()


def phone_line(wav: bytes) -> bytes:
    """8 kHz, 300-3400 Hz band, light compression: how it sounds on a call."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
            "-af", "highpass=f=300,lowpass=f=3400,acompressor=threshold=-18dB:ratio=3",
            "-ar", "8000", "-ac", "1", "-f", "wav", "pipe:1",
        ],
        input=wav, capture_output=True, check=True, timeout=30,
    )
    return proc.stdout
