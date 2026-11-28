import struct
from pathlib import Path

import numpy as np
import pytest

from ideo import boucles, cli, common, music


def chunk(kind: bytes, body: bytes) -> bytes:
    return kind + struct.pack(">q", len(body)) + body


def caf(category="Bass", key="E", beats=8, seconds=4.0, genre="Funk", signature="4/4") -> bytes:
    rate = 44100.0
    desc = struct.pack(">d", rate) + b"aac " + bytes(20)
    pakt = struct.pack(">qqii", 10, int(seconds * rate), 2112, 0)
    pairs = {"category": category, "key signature": key or "", "time signature": signature, "beat count": str(beats), "genre": genre}
    info = bytes(16) + bytes(4) + b"".join(k.encode() + b"\0" + v.encode() + b"\0" for k, v in pairs.items())
    return b"caff\x00\x01\x00\x00" + chunk(b"desc", desc) + chunk(b"pakt", pakt) + chunk(b"uuid", info) + chunk(b"data", b"\x00" * 8)


@pytest.fixture
def library(tmp_path, monkeypatch):
    folder = tmp_path / "loops"
    folder.mkdir()
    monkeypatch.setenv("IDEO_LOOPS", str(folder))
    boucles._index.cache_clear()
    yield folder
    boucles._index.cache_clear()


def add(folder: Path, name: str, **meta):
    (folder / f"{name}.caf").write_bytes(caf(**meta))


def test_read_takes_tempo_key_and_category_from_the_file(library):
    add(library, "Groove Bass", category="Bass", key="E", beats=8, seconds=4.0)
    loop = boucles.read(library / "Groove Bass.caf")
    assert loop["tempo"] == 120.0 and loop["key"] == "E" and loop["category"] == "Bass" and loop["style"] == "funk"


@pytest.mark.parametrize("meta", [{"beats": 6}, {"signature": "6/8"}, {"beats": 0}])
def test_read_refuses_loops_that_cannot_be_tiled(library, meta):
    add(library, "Odd", **meta)
    assert boucles.read(library / "Odd.caf") is None


def test_lead_and_effect_loops_are_left_out(library):
    add(library, "Funk Synth Lead 01", category="Keyboards")
    add(library, "Wipeout Synth FX", category="Keyboards")
    add(library, "Groove Piano", category="Keyboards")
    assert [l["name"] for l in boucles.index()] == ["Groove Piano"]


def test_a_style_needs_drums_bass_and_harmony_at_the_same_tempo_and_key(library):
    add(library, "Bass", category="Bass", key="E")
    add(library, "Piano", category="Keyboards", key="A")
    add(library, "Beat", category="Drums", key=None)
    assert boucles.styles() == []
    add(library, "Piano E", category="Keyboards", key="E")
    assert boucles.styles() == ["funk"]
    add(library, "Slow Guitar", category="Guitars", key="E", seconds=8.0, genre="Rock/Blues")
    add(library, "Slow Bass", category="Bass", key="E", seconds=8.0, genre="Rock/Blues")
    assert boucles.styles() == ["funk"]
    add(library, "Slow Beat", category="Drums", key=None, seconds=8.0, genre="Hip Hop")
    assert boucles.styles() == ["blues", "funk"]


def test_drums_of_the_same_style_come_first(library):
    add(library, "Bass", category="Bass")
    add(library, "Piano", category="Keyboards")
    add(library, "Funk Beat", category="Drums", key=None)
    add(library, "Other Beat", category="Drums", key=None, genre="Hip Hop")
    assert [l["name"] for l in boucles.combos(boucles.index(), "funk")[0]["drums"]] == ["Funk Beat"]


def test_pick_is_stable_for_a_job_and_a_style(library):
    for i in range(4):
        add(library, f"Bass {i}", category="Bass")
        add(library, f"Piano {i}", category="Keyboards")
        add(library, f"Beat {i}", category="Drums", key=None)
    loops = boucles.index()
    assert boucles.pick(loops, "funk", "job:funk") == boucles.pick(loops, "funk", "job:funk")
    with pytest.raises(common.IdeoError, match="Styles possibles : funk"):
        boucles.pick(loops, "jazz", "job:jazz")


def loop(name, category, beats=8, tempo=120.0):
    return {"path": f"/x/{name}.caf", "name": name, "category": category, "beats": beats, "tempo": tempo}


def test_compose_tiles_loops_on_the_beat_and_drops_drums_in_the_break():
    choice = {"tempo": 116.0, "key": "E", "drums": [loop("d", "Drums", 4, 116.0)], "bass": [loop("b", "Bass", 8, 116.0)],
              "harmony": [loop("h", "Keyboards", 16, 116.0)]}
    sources = {"/x/d.caf": 1.0, "/x/b.caf": 0.5, "/x/h.caf": 0.25}

    def decode(path):
        return np.full(200000, sources[str(path)], dtype=np.float32)

    out = boucles.compose(choice, 60, decode)
    section = 32 * 60 / 116 * music.RATE
    assert len(out) == int(round(4 * section))
    assert np.abs(out).max() == pytest.approx(0.9, abs=1e-6)
    middle = lambda i: out[int(i * section + section / 2)]
    assert middle(0) > middle(3) > 0


def test_layers_cycle_through_variants_without_duplicates():
    choice = {"drums": [1], "bass": [1, 2], "harmony": [1, 2]}
    plan = boucles.layers(choice, 4)
    assert plan[0] == [("drums", 0), ("bass", 0), ("harmony", 0)]
    assert plan[2] == [("drums", 0), ("bass", 1), ("harmony", 1)]
    assert plan[3] == [("bass", 0), ("harmony", 0)]


def test_choosing_loops_writes_the_track_its_choice_and_its_credit(library, tmp_path, monkeypatch):
    add(library, "Bass", category="Bass")
    add(library, "Piano", category="Keyboards")
    add(library, "Beat", category="Drums", key=None)
    monkeypatch.setattr(music, "decode", lambda path, work, log: np.sin(np.arange(96000, dtype=np.float32) / 20))
    job = tmp_path / "job"
    job.mkdir()
    said = music.choose_for(job, "boucles Funk")
    assert said.startswith("boucles Funk (120 bpm, E : ")
    target = job / "music-boucles-funk.wav"
    assert target.exists()
    assert music.read_choice(job) == {"choice": "boucles funk", "path": str(target.resolve())}
    assert music.selected(job) == ("choice", target.resolve())
    assert music.attribution(job, target.name) == "Musique : Composition Apple Loops (funk, 120 bpm, E)"


def test_loops_without_a_style_are_refused(library, tmp_path):
    with pytest.raises(common.IdeoError, match="boucles funk"):
        music.choose_for(tmp_path, "boucles")


def test_the_music_list_offers_the_loop_styles(library, monkeypatch, capsys):
    add(library, "Bass", category="Bass")
    add(library, "Piano", category="Keyboards")
    add(library, "Beat", category="Drums", key=None)
    monkeypatch.setattr(music, "listing", lambda: [])
    assert cli.main(["musique", "--liste"]) == 0
    assert capsys.readouterr().out.strip().splitlines()[-1] == "boucles <style>, composée sur place sans téléchargement : funk"


@pytest.mark.skipif(not boucles.ROOT.is_dir(), reason="Apple Loops absents")
def test_the_installed_library_offers_styles(monkeypatch):
    monkeypatch.delenv("IDEO_LOOPS", raising=False)
    assert "funk" in boucles.styles()
