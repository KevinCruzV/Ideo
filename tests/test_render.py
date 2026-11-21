import json
import math
import os
import shutil
import wave
from pathlib import Path

import pytest

from ideo import common, render

INFO = {
    "id": "abcdefghijk",
    "title": "Pourquoi on oublie",
    "channel": "Chaîne Test",
    "webpage_url": "https://www.youtube.com/watch?v=abcdefghijk",
    "duration": 1800,
}


@pytest.fixture
def job_sources(job_with_plan):
    common.save_json(job_with_plan / "info.json", INFO)
    plan = common.load_json(job_with_plan / "plan.json")
    plan["parts"][0]["scenes"][1]["src"] = "12:30"
    common.save_json(job_with_plan / "plan.json", plan)
    return job_with_plan


def two_part_plan(job):
    plan = common.load_json(job / "plan.json")
    second = json.loads(json.dumps(plan["parts"][0]))
    second["n"] = 2
    second["title"] = "La suite"
    plan["parts"].append(second)
    common.save_json(job / "plan.json", plan)


def test_sources_links_use_seconds(job_sources):
    path = render.write_sources(job_sources)
    text = path.read_text()
    assert path == job_sources / "out" / "sources.md"
    assert "watch?v=abcdefghijk&t=750s" in text
    assert "watch?v=abcdefghijk&t=2s" in text
    assert "shape-diagram" in text
    assert "Scène 2" in text


def test_sources_one_section_per_part(job_sources):
    two_part_plan(job_sources)
    text = render.write_sources(job_sources).read_text()
    assert text.count("## Partie") == 2


def test_description_credits_quoted_voices_not_channel(job_sources):
    text = render.write_description(job_sources, 1)
    assert text == "L'oubli\n\nVoix citées : Ebbinghaus\n"
    assert "Chaîne Test" not in text and "youtube" not in text
    assert "#" not in text
    assert (job_sources / "out" / "description.txt").read_text() == text


def test_description_lists_unique_speakers_in_order(job_sources):
    plan = common.load_json(job_sources / "plan.json")
    scenes = plan["parts"][0]["scenes"]
    quote = scenes[4]
    scenes.append(dict(quote, props={"text": quote["props"]["text"], "speaker": "France Inter"}))
    scenes.append(dict(quote))
    scenes.append(dict(quote, props={"text": quote["props"]["text"], "speaker": ""}))
    common.save_json(job_sources / "plan.json", plan)
    assert render.write_description(job_sources, 1) == "L'oubli\n\nVoix citées : Ebbinghaus, France Inter\n"


def test_description_without_named_voice_is_title_only(job_sources):
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["scenes"][4]["props"]["speaker"] = ""
    common.save_json(job_sources / "plan.json", plan)
    assert render.write_description(job_sources, 1) == "L'oubli\n"


def test_sources_never_print_channel(job_sources):
    assert "Chaîne Test" not in render.write_sources(job_sources).read_text()


def test_description_naming_with_several_parts(job_sources):
    two_part_plan(job_sources)
    render.write_description(job_sources, 2)
    assert (job_sources / "out" / "description-02.txt").read_text().startswith("La suite\n\n")
    assert not (job_sources / "out" / "description.txt").exists()


def prepare_render(job, frames=120):
    part_dir = job / "parts" / "01"
    part_dir.mkdir(parents=True, exist_ok=True)
    (part_dir / "part.wav").write_bytes(b"x")
    common.save_json(part_dir / "timeline.json", {"durationInFrames": frames})


def fake_run(calls):
    def run(cmd, log):
        calls.append(cmd)
        out = next(c for c in cmd if c.endswith(".mp4"))
        Path(out).write_bytes(b"mp4")

    return run


GOOD = {"width": 1080, "height": 1920, "fps": 30.0, "duration": 4.0, "video_codec": "h264", "has_audio": True}


def test_single_part_renders_video_mp4(job_sources, monkeypatch):
    calls = []
    prepare_render(job_sources, 120)
    monkeypatch.setattr(common, "run", fake_run(calls))
    monkeypatch.setattr(render, "probe_media", lambda p: dict(GOOD))
    out = render.render_part(job_sources, 1)
    assert out == job_sources / "out" / "video.mp4"
    cmd = calls[0]
    assert cmd[1:3] == ["--dir", str(render.REPO / "render")]
    assert cmd[3:7] == ["exec", "remotion", "render", "Short"]
    assert f"--public-dir={job_sources / 'parts' / '01'}" in cmd
    assert f"--props={job_sources / 'parts' / '01' / 'timeline.json'}" in cmd
    assert common.read_status(job_sources)["steps"]["render-01"]["ok"] is True


def test_several_parts_render_partie_mp4(job_sources, monkeypatch):
    two_part_plan(job_sources)
    prepare_render(job_sources, 120)
    monkeypatch.setattr(common, "run", fake_run([]))
    monkeypatch.setattr(render, "probe_media", lambda p: dict(GOOD))
    assert render.render_part(job_sources, 1) == job_sources / "out" / "partie-01.mp4"


def test_render_is_idempotent(job_sources, monkeypatch):
    calls = []
    prepare_render(job_sources, 120)
    monkeypatch.setattr(common, "run", fake_run(calls))
    monkeypatch.setattr(render, "probe_media", lambda p: dict(GOOD))
    render.render_part(job_sources, 1)
    render.render_part(job_sources, 1)
    assert len(calls) == 1
    timeline = job_sources / "parts" / "01" / "timeline.json"
    future = timeline.stat().st_mtime + 10
    os.utime(timeline, (future, future))
    render.render_part(job_sources, 1)
    assert len(calls) == 2


@pytest.mark.parametrize(
    "override, message",
    [
        ({"duration": 5.0}, "dure"),
        ({"has_audio": False}, "audio"),
        ({"video_codec": None, "width": None, "height": None}, "vidéo"),
        ({"width": 720, "height": 1280}, "720x1280"),
    ],
)
def test_render_fails_when_probe_rejects(job_sources, monkeypatch, override, message):
    prepare_render(job_sources, 120)
    monkeypatch.setattr(common, "run", fake_run([]))
    monkeypatch.setattr(render, "probe_media", lambda p: {**GOOD, **override})
    with pytest.raises(common.IdeoError, match=message):
        render.render_part(job_sources, 1)
    assert common.read_status(job_sources)["steps"]["render-01"]["ok"] is False


def test_render_requires_pnpm(job_sources, monkeypatch):
    prepare_render(job_sources, 120)
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(common.IdeoError, match="pnpm"):
        render.render_part(job_sources, 1)


def write_tone(path, seconds, rate=48000):
    n = int(rate * seconds)
    frames = b"".join(
        int(6000 * math.sin(2 * math.pi * 330 * i / rate)).to_bytes(2, "little", signed=True) for i in range(n)
    )
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames)


@pytest.fixture
def job_with_timeline_fixture(job_sources):
    part_dir = job_sources / "parts" / "01"
    part_dir.mkdir(parents=True, exist_ok=True)
    write_tone(part_dir / "part.wav", 4.0)
    words = [
        {"w": "Dis-moi", "from": 0, "to": 15},
        {"w": "pourquoi", "from": 15, "to": 30},
        {"w": "tu", "from": 30, "to": 40},
        {"w": "oublies", "from": 40, "to": 60},
    ]
    timeline = {
        "fps": 30, "width": 1080, "height": 1920, "durationInFrames": 120, "lang": "fr",
        "audio": "part.wav", "watermark": "Ideo",
        "chapter": {"part": 1, "total": 1, "title": "L'oubli", "label": "Partie"},
        "segments": [
            {"kind": "hook", "from": 0, "to": 45, "props": {"text": "Dis-moi pourquoi tu oublies"}, "items": []},
            {"kind": "scene", "type": "shape-diagram", "from": 45, "to": 90, "props": {},
             "items": [{"el": "values.0", "at": 55}]},
            {"kind": "outro", "from": 90, "to": 120, "props": {"text": "Abonne-toi pour la suite."}},
        ],
        "captions": [{"words": words, "from": 0, "to": 60}],
    }
    common.save_json(part_dir / "timeline.json", timeline)
    return job_sources


@pytest.mark.slow
def test_render_fixture_part(job_with_timeline_fixture):
    job = job_with_timeline_fixture
    mp4 = render.render_part(job, 1)
    assert mp4 == job / "out" / "video.mp4"
    probe = render.probe_media(mp4)
    assert (probe["width"], probe["height"], probe["fps"]) == (1080, 1920, 30)
    assert abs(probe["duration"] - 4.0) < 0.1
    assert probe["has_audio"] is True
    assert (job / "logs" / "render-01.log").exists()
