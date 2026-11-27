import json
import math
import os
import shutil
import time
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


def test_render_is_redone_when_the_render_code_changed_since(job_sources, monkeypatch):
    calls = []
    prepare_render(job_sources, 120)
    monkeypatch.setattr(common, "run", fake_run(calls))
    monkeypatch.setattr(render, "probe_media", lambda p: dict(GOOD))
    render.render_part(job_sources, 1)
    render.render_part(job_sources, 1)
    assert len(calls) == 1
    monkeypatch.setattr(render, "_render_src_version", lambda: time.time() + 3600)
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
        "audio": "part.wav", "watermark": "@idevideos",
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


def test_real_duration_outside_bounds_is_flagged_in_progress_log(job_sources, monkeypatch):
    prepare_render(job_sources, 120)
    monkeypatch.setattr(common, "run", fake_run([]))
    monkeypatch.setattr(render, "probe_media", lambda p: dict(GOOD))
    render.render_part(job_sources, 1)
    log = (job_sources / "logs" / "progress.log").read_text(encoding="utf-8")
    assert "ATTENTION partie 01 : durée réelle 4.0 s, hors de 65 à 300 s" in log


def test_real_duration_inside_bounds_is_not_flagged(job_sources, monkeypatch):
    prepare_render(job_sources, 2700)
    monkeypatch.setattr(common, "run", fake_run([]))
    monkeypatch.setattr(render, "probe_media", lambda p: {**GOOD, "duration": 90.0})
    render.render_part(job_sources, 1)
    progress = job_sources / "logs" / "progress.log"
    assert not progress.exists() or "ATTENTION" not in progress.read_text(encoding="utf-8")


@pytest.mark.parametrize("lang,label", [("fr", "Voix citées : "), ("en", "Quoted voices: "), ("de", "Zitierte Stimmen: ")])
def test_description_voices_label_follows_the_language(job_sources, lang, label):
    plan = common.load_json(job_sources / "plan.json")
    plan["lang"] = lang
    common.save_json(job_sources / "plan.json", plan)
    assert render.write_description(job_sources, 1) == f"L'oubli\n\n{label}Ebbinghaus\n"


def fake_still(calls):
    def run(cmd, log):
        calls.append(cmd)
        out = next(c for c in cmd if c.endswith(".png"))
        Path(out).write_bytes(b"png")

    return run


def test_cover_props_take_title_hook_and_first_picto(job_sources):
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["scenes"][0]["props"].pop("picto", None)
    plan["parts"][0]["scenes"][1]["props"]["picto"] = "brain"
    plan["mood"] = "dark"
    common.save_json(job_sources / "plan.json", plan)
    props = render.cover_props(plan, plan["parts"][0])
    assert props["title"] == plan["parts"][0]["title"]
    assert props["hook"] == plan["parts"][0]["hook"]
    assert props["picto"] == "brain"
    assert "watermark" not in props
    assert props["mood"] == "dark"
    assert props["part"] == 1 and props["total"] == 1


def test_cover_picto_also_comes_from_versus_and_grids():
    part = {"scenes": [{"type": "versus", "props": {"left": "A", "right": "B", "right_picto": "eye"}},
                       {"type": "key-title", "props": {"picto": "sun"}}]}
    assert render.cover_picto(part) == "eye"
    grid = {"scenes": [{"type": "icon-grid", "props": {"cells": [{"shape": "circle", "label": "x"}, {"picto": "eye", "label": "y"}]}}]}
    assert render.cover_picto(grid) == "eye"
    assert render.cover_picto({"scenes": [{"type": "stamp", "props": {"text": "x"}}]}) is None


def test_cover_prefers_the_subject_over_a_flag():
    grid = {"scenes": [{"type": "icon-grid", "props": {"cells": [{"picto": "flag:ar", "label": "x"}, {"picto": "globe", "label": "y"}]}}]}
    assert render.cover_picto(grid) == "globe"
    later = {"scenes": [{"type": "versus", "props": {"left": "A", "right": "B", "left_picto": "flag:us", "right_picto": "flag:su"}},
                        {"type": "key-title", "props": {"picto": "coin"}}]}
    assert render.cover_picto(later) == "coin"
    only_flags = {"scenes": [{"type": "versus", "props": {"left": "A", "right": "B", "left_picto": "flag:us", "right_picto": "flag:su"}}]}
    assert render.cover_picto(only_flags) == "flag:us"


def store_photo(job, person, image="photo.jpg"):
    common.save_json(job / Path(image).with_suffix(".json").name, {"person": person, "extension": Path(image).suffix[1:]})
    (job / image).write_bytes(b"jpg")


def person_card(name, photo=True):
    props = {"name": name, "role": "savant"}
    if photo:
        props["photo"] = True
    return {"type": "person-card", "say": "x", "props": props}


def test_cover_shows_the_photo_of_the_main_person(job_sources):
    store_photo(job_sources, "Hermann Ebbinghaus")
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["scenes"].append(person_card("Hermann Ebbinghaus"))
    props = render.cover_props(plan, plan["parts"][0], job_sources)
    assert props["photo"] == "photo.jpg"
    assert "photo" not in render.cover_props(plan, plan["parts"][0])


def test_cover_has_no_photo_without_a_photo_card_or_a_stored_photo(job_sources):
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["scenes"].append(person_card("Hermann Ebbinghaus", photo=False))
    assert "photo" not in render.cover_props(plan, plan["parts"][0], job_sources)
    plan["parts"][0]["scenes"].append(person_card("Hermann Ebbinghaus"))
    assert "photo" not in render.cover_props(plan, plan["parts"][0], job_sources)


def test_cover_look_comes_from_the_first_person_card(job_sources):
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["scenes"].append({
        "type": "person-card", "say": "x",
        "props": {"name": "Hermann Ebbinghaus", "role": "savant", "gender": "man", "age": "old", "hat": "top-hat"},
    })
    look = render.cover_look(plan["parts"][0])
    assert look == {"name": "Hermann Ebbinghaus", "gender": "man", "age": "old", "hat": "top-hat"}


def test_cover_look_is_none_without_a_person_card():
    assert render.cover_look({"scenes": [{"type": "stamp", "props": {"text": "x"}}]}) is None


def test_cover_props_fall_back_to_the_main_person_look_without_a_photo(job_sources):
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["scenes"].append(person_card("Hermann Ebbinghaus", photo=False))
    props = render.cover_props(plan, plan["parts"][0], job_sources)
    assert "photo" not in props
    assert props["look"] == {"name": "Hermann Ebbinghaus"}


def test_cover_props_prefer_the_real_photo_over_a_drawn_look(job_sources):
    store_photo(job_sources, "Hermann Ebbinghaus")
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["scenes"].append(person_card("Hermann Ebbinghaus"))
    props = render.cover_props(plan, plan["parts"][0], job_sources)
    assert props["photo"] == "photo.jpg"
    assert "look" not in props


def test_cover_takes_the_first_person_who_has_a_photo(job_sources):
    store_photo(job_sources, "Hermann Ebbinghaus")
    store_photo(job_sources, "Marie Curie", "photo-marie-curie.jpg")
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["scenes"] += [person_card("Marie Curie"), person_card("Hermann Ebbinghaus")]
    assert render.cover_props(plan, plan["parts"][0], job_sources)["photo"] == "photo-marie-curie.jpg"


def test_cover_still_can_read_the_photo_from_the_part_folder(job_sources, monkeypatch):
    store_photo(job_sources, "Hermann Ebbinghaus")
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["scenes"].append(person_card("Hermann Ebbinghaus"))
    common.save_json(job_sources / "plan.json", plan)
    calls = []
    monkeypatch.setattr(common, "run", fake_still(calls))
    render.write_cover(job_sources, 1)
    part_dir = job_sources / "parts" / "01"
    assert common.load_json(part_dir / "cover.json")["photo"] == "photo.jpg"
    assert (part_dir / "photo.jpg").read_bytes() == b"jpg"
    assert f"--public-dir={part_dir}" in calls[0]


def test_cover_renders_a_still_of_the_cover_composition(job_sources, monkeypatch):
    calls = []
    monkeypatch.setattr(common, "run", fake_still(calls))
    out = render.write_cover(job_sources, 1)
    assert out == job_sources / "out" / "cover.png" and out.read_bytes() == b"png"
    cmd = calls[0]
    assert cmd[3:7] == ["exec", "remotion", "still", "Cover"]
    assert f"--props={job_sources / 'parts' / '01' / 'cover.json'}" in cmd
    assert f"--frame={render.COVER_FRAME}" in cmd


def test_cover_is_not_rendered_again_when_nothing_changed(job_sources, monkeypatch):
    calls = []
    monkeypatch.setattr(common, "run", fake_still(calls))
    render.write_cover(job_sources, 1)
    render.write_cover(job_sources, 1)
    assert len(calls) == 1
    plan = common.load_json(job_sources / "plan.json")
    plan["parts"][0]["title"] = "Un autre titre"
    common.save_json(job_sources / "plan.json", plan)
    render.write_cover(job_sources, 1)
    assert len(calls) == 2


def test_cover_is_rendered_again_when_the_render_code_changed_since(job_sources, monkeypatch):
    calls = []
    monkeypatch.setattr(common, "run", fake_still(calls))
    render.write_cover(job_sources, 1)
    assert len(calls) == 1
    monkeypatch.setattr(render, "_render_src_version", lambda: time.time() + 3600)
    render.write_cover(job_sources, 1)
    assert len(calls) == 2


def test_several_parts_get_one_cover_each(job_sources, monkeypatch):
    two_part_plan(job_sources)
    monkeypatch.setattr(common, "run", fake_still([]))
    assert render.write_cover(job_sources, 2) == job_sources / "out" / "cover-02.png"
    props = common.load_json(job_sources / "parts" / "02" / "cover.json")
    assert props["part"] == 2 and props["total"] == 2 and props["title"] == "La suite"


def test_cover_without_output_is_an_error(job_sources, monkeypatch):
    monkeypatch.setattr(common, "run", lambda cmd, log: None)
    with pytest.raises(common.IdeoError, match="couverture"):
        render.write_cover(job_sources, 1)


def test_cover_look_prefers_the_person_named_by_the_hook():
    part = {"hook": "Le Christ cosmique veut devenir président", "scenes": [
        {"type": "person-card", "props": {"name": "Nathalie Arthaud", "role": "Lutte ouvrière", "gender": "woman"}},
        {"type": "person-card", "props": {"name": "Sylvain Durif", "role": "Se dit « Christ cosmique »", "hair": "wild"}},
    ]}
    assert render.cover_look(part) == {"name": "Sylvain Durif", "hair": "wild"}


def test_cover_look_keeps_the_first_card_when_the_hook_names_nobody():
    part = {"hook": "Pourquoi tant de candidats ?", "scenes": [
        {"type": "person-card", "props": {"name": "Nathalie Arthaud"}},
        {"type": "person-card", "props": {"name": "Sylvain Durif"}},
    ]}
    assert render.cover_look(part) == {"name": "Nathalie Arthaud"}
