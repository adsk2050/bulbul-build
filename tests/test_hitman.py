"""Bulbul Flash Cricket at /bulbul-flash/ (the 3D game): served, with its rules."""

from __future__ import annotations

from test_app import client  # noqa: F401  (fixture)

from bulbul_build.commentary import game_rules


def test_page_redirects_to_directory(client):  # noqa: F811
    c, _ = client
    r = c.get("/bulbul-flash", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/bulbul-flash/"


def test_old_names_are_gone(client):  # noqa: F811
    c, _ = client
    for old in ("/hitman", "/hitman/", "/gully-bhaiya", "/gully-bhaiya/"):
        assert c.get(old, follow_redirects=False).status_code == 404


def test_hitman_page_served_with_voice_and_credit(client):  # noqa: F811
    c, _ = client
    r = c.get("/bulbul-flash/")
    assert r.status_code == 200
    assert "/static/hitman-voice.js" in r.text
    assert "ekcuttingchaidesign" in r.text
    # The game bundles its own font; scripts stay same-origin only.
    csp = r.headers["content-security-policy"]
    assert "font-src 'self'" in csp
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp.split("script-src")[1]
    assert "Hitman" not in r.text.split("<body>")[0]  # not in the title or meta
    assert "Bhaiya" not in r.text
    assert c.get("/bulbul-flash/CREDITS.txt").status_code == 200
    assert c.get("/static/hitman-voice.js").status_code == 200


def test_hitman_rules_loaded_for_commentator():
    rules = game_rules("hitman")
    assert "Bulbul Flash Cricket" in rules and "Hitman" not in rules and "Bhaiya" not in rules
    assert "in_air" in rules and "timing_ms" in rules


def test_game_only_site_serves_nothing_else(client, monkeypatch):  # noqa: F811
    from bulbul_build import app as app_mod

    c, _ = client
    monkeypatch.setattr(app_mod, "GAME_ONLY", True)
    assert c.get("/bulbul-flash/").status_code == 200
    assert c.get("/static/hitman-reel.js").status_code == 200
    r = c.get("/", follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == "/bulbul-flash/"
    for path in ("/talk", "/cricket", "/m/udhaar-wapas", "/api/modes", "/api/budget"):
        assert c.get(path).status_code == 404, path
    assert c.post("/api/udhaar-wapas", json={}).status_code == 404
