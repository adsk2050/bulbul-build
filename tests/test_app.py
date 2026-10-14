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
