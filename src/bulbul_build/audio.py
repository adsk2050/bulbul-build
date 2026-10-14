"""Join WAV clips and make the phone-line version, with ffmpeg."""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path


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


def share_mp4(recording: bytes, suffix: str) -> bytes:
    """A browser recording (WebM or MP4) as a WhatsApp-friendly MP4: H.264 + AAC, 720x1280.

    Browsers write MP4s with no duration in the header and WebM that some
    phones will not play; one ffmpeg pass fixes both.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / f"in{suffix}", Path(tmp) / "out.mp4"
        src.write_bytes(recording)
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(src),
                "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,fps=30",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", "-t", "30",
                str(dst),
            ],
            capture_output=True, check=True, timeout=60,
        )
        return dst.read_bytes()
