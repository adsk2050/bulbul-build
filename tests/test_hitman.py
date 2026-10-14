"""Hitman Cricket at /hitman/: the built game is served, and Gully Bhaiya has its rules."""

from __future__ import annotations

from test_app import client  # noqa: F401  (fixture)

from bulbul_build.commentary import game_rules


def test_hitman_redirects_to_directory(client):  # noqa: F811
    c, _ = client
    r = c.get("/hitman", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/hitman/"


def test_hitman_page_served_with_voice_and_credit(client):  # noqa: F811
    c, _ = client
    r = c.get("/hitman/")
    assert r.status_code == 200
    assert "/static/hitman-voice.js" in r.text
    assert "ekcuttingchaidesign" in r.text
    # The game bundles its own font; scripts stay same-origin only.
    csp = r.headers["content-security-policy"]
    assert "font-src 'self'" in csp
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp.split("script-src")[1]
    assert c.get("/hitman/CREDITS.txt").status_code == 200
    assert c.get("/static/hitman-voice.js").status_code == 200


def test_hitman_rules_loaded_for_commentator():
    rules = game_rules("hitman")
    assert "Hitman Cricket" in rules
    assert "in_air" in rules and "timing_ms" in rules
