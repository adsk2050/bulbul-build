"""End-to-end through the FastAPI app with Sarvam mocked."""

from __future__ import annotations

import os

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from test_core import tts_response


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")
    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "ledger.sqlite"))
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("PER_IP_PER_MIN", "100")
    import importlib

    import bulbul_build.app as appmod

    appmod = importlib.reload(appmod)
    with respx.mock(assert_all_called=False) as mock:
        mock.post("https://api.sarvam.ai/text-to-speech").mock(side_effect=tts_response)
        mock.route(host="testserver").pass_through()
        with TestClient(appmod.app) as c:
            yield c, mock


def test_modes_listed(client):
    c, _ = client
    slugs = [m["slug"] for m in c.get("/api/modes").json()]
    assert "udhaar-wapas" in slugs


def test_udhaar_hinglish_end_to_end(client):
    c, mock = client
    r = c.post("/api/udhaar-wapas", json={"friend": "Rahul", "amount": 850, "reason": "Garba pass", "since": "Navratri", "upi": "anmol@okhdfc"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "₹850" in data["title"]
    assert data["audio_url"].startswith("/audio/") and data["phone_audio_url"]
    assert c.get(data["audio_url"]).status_code == 200
    assert all(cap["end"] > cap["start"] for cap in data["captions"])


def test_bad_input_rejected(client):
    c, _ = client
    r = c.post("/api/udhaar-wapas", json={"friend": "", "amount": -5})
    assert r.status_code == 422


def test_audio_path_traversal_blocked(client):
    c, _ = client
    assert c.get("/audio/..%2F..%2F.env").status_code == 404


def test_security_headers(client):
    c, _ = client
    r = c.get("/")
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in r.headers["content-security-policy"]


def _fake_recording(tmp_path) -> bytes:
    """A 1 s 9:16 WebM with sound, like the browser's MediaRecorder output."""
    import subprocess

    out = tmp_path / "rec.webm"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=540x960:rate=30",
         "-f", "lavfi", "-i", "sine=frequency=440", "-t", "1", "-c:v", "libvpx", "-c:a", "libopus", str(out)],
        check=True,
    )
    return out.read_bytes()


def test_share_clip_becomes_h264_mp4(client, tmp_path):
    c, _ = client
    r = c.post("/api/clip", content=_fake_recording(tmp_path), headers={"Content-Type": "video/webm"})
    assert r.status_code == 200, r.text
    mp4 = c.get(r.json()["url"])
    assert mp4.status_code == 200 and mp4.headers["content-type"] == "video/mp4"
    assert b"ftyp" in mp4.content[:16] and b"avc1" in mp4.content[:4096]


def test_share_clip_rejects_other_types(client):
    c, _ = client
    assert c.post("/api/clip", content=b"x", headers={"Content-Type": "text/plain"}).status_code == 415
