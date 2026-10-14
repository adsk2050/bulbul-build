"""Bulbul Lab: every lesson builds, stays cheap, uses real voices and labels its clips.

No test reaches Sarvam: the end-to-end test mocks HTTP with respx.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from bulbul_build.modes import REGISTRY
from bulbul_build.modes.bulbul_lab import LESSONS, MAX_CHARS, MODE, Form, build
from test_app import client  # noqa: F401  (fixture)

ROOT = Path(__file__).resolve().parents[1]
API_VOICES = set((ROOT / "docs" / "voices-api.txt").read_text().split())
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
LABEL = re.compile(r"^[A-J] · \S")


@pytest.fixture(params=list(LESSONS))
async def script(request):
    return request.param, await build(Form(lesson=request.param), sarvam=None)


async def test_lesson_builds(script):
    key, s = script
    assert s.title == LESSONS[key].title
    assert s.card["kicker"].startswith("BULBUL LAB · LESSON ")
    assert s.card["emoji"] == "🧪" and s.card["course_ref"].startswith("CS224S Lecture ")
    assert s.share_text and len(s.lines) >= 2


async def test_voices_exist_on_api(script):
    _, s = script
    assert {line.speaker for line in s.lines} <= API_VOICES


async def test_spoken_chars_within_budget(script):
    key, s = script
    total = sum(len(line.text) for line in s.lines)
    assert total == LESSONS[key].spoken_chars() <= MAX_CHARS


async def test_clips_are_labelled(script):
    key, s = script
    clips = s.lines[1 : 1 + len(LESSONS[key].clips)]
    assert [c.caption[0] for c in clips] == [chr(ord("A") + i) for i in range(len(clips))]
    assert all(LABEL.match(c.caption) for c in clips)
    assert s.card["clips"] == [c.caption.split(":")[0] for c in clips]


async def test_scripts_follow_language_rules(script):
    _, s = script
    for line in s.lines:
        if line.language == "en-IN":
            assert not DEVANAGARI.search(line.text), line.text
        assert 0.5 <= line.pace <= 2.0


async def test_lesson_specifics():
    pace = await build(Form(lesson="pace"), None)
    assert [ln.pace for ln in pace.lines[1:]] == [0.5, 1.0, 2.0]
    phone = await build(Form(lesson="phone"), None)
    assert phone.phone_line
    styles = await build(Form(lesson="styles"), None)
    assert len({ln.speaker.split("_")[0] for ln in styles.lines[1:]}) == 1  # one speaker, four styles
    langs = await build(Form(lesson="languages"), None)
    assert len({ln.language for ln in langs.lines[1:]}) == 9  # Hinglish shares hi-IN
    script_ = await build(Form(lesson="script"), None)
    assert DEVANAGARI.search(script_.lines[1].text) and not DEVANAGARI.search(script_.lines[2].text)


def test_form_labels_every_lesson():
    schema = Form.model_json_schema()
    assert set(schema["properties"]["lesson"]["x-labels"]) == set(LESSONS)


def test_end_to_end(client, monkeypatch):  # noqa: F811
    c, mock = client
    monkeypatch.setitem(REGISTRY, MODE.slug, MODE)
    r = c.post("/api/bulbul-lab", json={"lesson": "phone"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["card"]["kicker"] == "BULBUL LAB · LESSON 8"
    assert data["phone_audio_url"] and c.get(data["audio_url"]).status_code == 200
    calls = mock.routes[0].call_count
    assert calls == len(LESSONS["phone"].clips) + 2  # intro + clip + outro
    r2 = c.post("/api/bulbul-lab", json={"lesson": "phone"})
    assert r2.status_code == 200 and mock.routes[0].call_count == calls  # served from cache
    assert c.post("/api/bulbul-lab", json={"lesson": "nope"}).status_code == 422
