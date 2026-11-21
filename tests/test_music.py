import json
import wave
from pathlib import Path

import numpy as np
import pytest

from ideo import assemble, common, config, history, music

RATE = 48000


def tone_track(path, seconds=20.0, freq=220.0, amp=0.3, calm_intro=0.0):
    t = np.arange(int(seconds * RATE)) / RATE
    wave_ = amp * np.sin(2 * np.pi * freq * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t) ** 2)
    if calm_intro:
        wave_[:int(calm_intro * RATE)] *= 0.05
    music.write_wav(Path(path), wave_.astype(np.float32))
    return Path(path)


@pytest.fixture
def library(tmp_path):
    folder = tmp_path / "musique"
    folder.mkdir()
    for name in ("alpha.wav", "beta.wav", "gamma.wav", "delta.wav", "epsilon.wav"):
        tone_track(folder / name, seconds=12.0)
    (folder / "LICENCE.txt").write_text("Musique en domaine public (CC0 1.0), par Holizna, depuis OpenGameArt.\n", encoding="utf-8")
    return folder


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    return tmp_path / "home"


def write_config(home, data):
    (home / "config.json").write_text(json.dumps(data), encoding="utf-8")


def test_tracks_lists_supported_files_sorted_and_ignores_the_rest(library):
    (library / "_extrait").mkdir()
    (library / "_note.wav").write_bytes(b"x")
    (library / "notes.txt").write_text("x", encoding="utf-8")
    (library / "zeta.mp3").write_bytes(b"x")
    assert [t.name for t in music.tracks(library)] == ["alpha.wav", "beta.wav", "delta.wav", "epsilon.wav", "gamma.wav", "zeta.mp3"]
    assert music.tracks(library / "absent") == []


def test_choice_is_reproducible_and_depends_on_the_job(library):
    available = music.tracks(library)
    assert music.choose("ZcOLpOS-QcY", available, []) == music.choose("ZcOLpOS-QcY", available, [])
    picks = {music.choose(f"job{i}", available, []).name for i in range(40)}
    assert len(picks) >= 3


def test_choice_avoids_the_recent_tracks_when_possible(library):
    available = music.tracks(library)
    first = music.choose("job1", available, []).name
    other = music.choose("job1", available, [first]).name
    assert other != first
    recent = [t.name for t in available[:3]]
    assert music.choose("job1", available, recent).name not in recent
    assert music.choose("job1", available, [t.name for t in available]) in available
    assert music.choose("job1", [], []) is None


def test_recent_music_comes_from_the_last_three_other_jobs(home):
    for i, name in enumerate(["a.mp3", "b.mp3", "c.mp3", "d.mp3"]):
        history.set_music(f"job{i}", name)
    history.set_music("current", "z.mp3")
    assert history.recent_music("current", 3) == ["d.mp3", "c.mp3", "b.mp3"]
    assert history.recent_music("job3", 3) == ["z.mp3", "c.mp3", "b.mp3"]


def test_calm_intro_is_skipped_but_a_lively_start_is_kept():
    t = np.arange(40 * RATE) / RATE
    lively = (0.3 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)
    assert music.start_offset(lively) == 0.0
    calm = lively.copy()
    calm[:12 * RATE] *= 0.03
    offset = music.start_offset(calm)
    assert 9 <= offset <= 13
    assert music.start_offset(np.zeros(5 * RATE, dtype=np.float32)) == 0.0


def test_bed_loops_with_a_crossfade_and_has_the_right_length():
    samples = (0.3 * np.sin(2 * np.pi * 200 * np.arange(6 * RATE) / RATE)).astype(np.float32)
    out = music.bed(samples, 0.0, 20 * RATE)
    assert len(out) == 20 * RATE
    seam = 6 * RATE - int(music.CROSSFADE * RATE)
    assert np.max(np.abs(np.diff(out[seam - 100:seam + int(music.CROSSFADE * RATE) + 100]))) < 0.2
    assert len(music.bed(samples, 2.0, 3 * RATE)) == 3 * RATE


def test_fades():
    gain = music.fades(10 * RATE)
    assert gain[0] == 0.0 and gain[-1] == 0.0 and gain[5 * RATE] == 1.0
    assert gain[int(1.5 * RATE) - 200] < 1.0 and gain[int(1.5 * RATE) + 5] == 1.0
    assert gain[-int(2.0 * RATE) + 5] < 1.0 and gain[-int(2.0 * RATE) - 5] == 1.0
    assert len(music.fades(RATE)) == RATE


def test_envelope_levels_follow_speech_pauses_and_source_clips():
    length = 30 * RATE
    env = music.envelope(length, [(0.0, 8.0), (12.0, 20.0)], [(22.0, 26.0)])
    db = lambda t: 20 * np.log10(env[int(t * RATE)])
    assert abs(db(4.0)) < 0.5 and abs(db(16.0)) < 0.5
    assert db(10.0) == pytest.approx(8.0, abs=0.5)
    assert db(24.0) == pytest.approx(-6.0, abs=0.5)
    assert db(29.0) == pytest.approx(8.0, abs=0.5)
    assert abs(db(8.01) - db(8.0)) < 0.5 and db(7.8) < db(8.0) < db(8.2)


def test_attribution_with_and_without_the_licence_file(library, tmp_path):
    assert music.attribution(library, "city-in-the-rearview.mp3") == "Musique : City in the rearview, par Holizna, domaine public (CC0)"
    (library / "LICENCE.txt").write_text("Usage libre.\n", encoding="utf-8")
    assert music.attribution(library, "city-in-the-rearview.mp3") == "Musique : city-in-the-rearview.mp3"
    (library / "LICENCE.txt").unlink()
    assert music.attribution(library, "autumn.mp3") == "Musique : autumn.mp3"


def test_config_defaults_and_keys(home, tmp_path):
    assert config.music_enabled() is True and config.music_level_db() == -20
    assert config.music_dir() == home / "musique"
    write_config(home, {"music": False, "music_dir": str(tmp_path / "x"), "music_level_db": -25})
    assert config.music_enabled() is False and config.music_dir() == tmp_path / "x" and config.music_level_db() == -25
    write_config(home, {"music_dir": "sons"})
    assert config.music_dir() == home / "sons"


@pytest.mark.parametrize("content", [{"music": "oui"}, {"music_dir": ""}, {"music_dir": 3}, {"music_level_db": "bas"},
                                     {"music_level_db": 0}, {"music_level_db": -60}, {"music_level_db": True}])
def test_config_errors(home, content):
    write_config(home, content)
    with pytest.raises(common.IdeoError, match="config.json"):
        config.music_enabled()


def loudness(path):
    return assemble._integrated(Path(path))


def assembled(job, library, home, **cfg):
    write_config(home, {"music_dir": str(library), **cfg})
    return assemble.assemble_part(job, 1)


def test_music_is_mixed_at_minus_14_lufs_with_a_chosen_track(job_with_voice_fixtures, library, home):
    job = job_with_voice_fixtures
    out = assembled(job, library, home)
    assert loudness(out) == pytest.approx(-14.0, abs=0.5)
    info = common.load_json(job / "parts" / "01" / "music.json")
    assert info["track"] in {t.name for t in music.tracks(library)}
    assert info["voice_lufs"] is not None and info["music_under_voice_lufs"] is not None
    assert info["music_under_voice_lufs"] == pytest.approx(info["voice_lufs"] - 20, abs=2.5)
    assert history.load()["jobs"][job.name]["music"] == info["track"]


def test_level_follows_the_config(job_with_voice_fixtures, library, home):
    job = job_with_voice_fixtures
    assembled(job, library, home, music_level_db=-30)
    info = common.load_json(job / "parts" / "01" / "music.json")
    assert info["music_under_voice_lufs"] == pytest.approx(info["voice_lufs"] - 30, abs=2.5)


def test_disabled_or_empty_folder_means_no_music(job_with_voice_fixtures, tmp_path, home):
    job = job_with_voice_fixtures
    write_config(home, {"music": False})
    assemble.assemble_part(job, 1)
    assert common.load_json(job / "parts" / "01" / "music.json")["track"] is None
    empty = tmp_path / "vide"
    empty.mkdir()
    write_config(home, {"music_dir": str(empty)})
    assemble.assemble_part(job, 1)
    info = common.load_json(job / "parts" / "01" / "music.json")
    assert info["track"] is None and info["missing"] is True
    write_config(home, {"music_dir": str(tmp_path / "absent")})
    assemble.assemble_part(job, 1)
    assert common.load_json(job / "parts" / "01" / "music.json")["missing"] is True


def test_the_track_stays_the_same_when_the_part_is_reassembled(job_with_voice_fixtures, library, home):
    job = job_with_voice_fixtures
    assembled(job, library, home)
    first = common.load_json(job / "parts" / "01" / "music.json")["track"]
    (job / "parts" / "01" / "part.wav").unlink()
    history.set_music("other-job", first)
    assemble.assemble_part(job, 1)
    assert common.load_json(job / "parts" / "01" / "music.json")["track"] == first


def test_changing_the_music_settings_rebuilds_the_part(job_with_voice_fixtures, library, home):
    job = job_with_voice_fixtures
    assembled(job, library, home)
    before = (job / "parts" / "01" / "part.wav").stat().st_mtime_ns
    assemble.assemble_part(job, 1)
    assert (job / "parts" / "01" / "part.wav").stat().st_mtime_ns == before
    write_config(home, {"music_dir": str(library), "music_level_db": -26})
    assemble.assemble_part(job, 1)
    assert (job / "parts" / "01" / "part.wav").stat().st_mtime_ns != before


def test_offsets_do_not_change_with_music(job_with_voice_fixtures, library, home):
    job = job_with_voice_fixtures
    write_config(home, {"music": False})
    assemble.assemble_part(job, 1)
    plain = (job / "parts" / "01" / "offsets.json").read_text(encoding="utf-8")
    assembled(job, library, home)
    assert (job / "parts" / "01" / "offsets.json").read_text(encoding="utf-8") == plain


def test_sources_md_gets_the_music_line(job_with_voice_fixtures, library, home):
    from ideo import render

    job = job_with_voice_fixtures
    common.save_json(job / "info.json", {"id": "abcdefghijk", "duration": 120})
    assembled(job, library, home)
    track = common.load_json(job / "parts" / "01" / "music.json")["track"]
    text = render.write_sources(job).read_text(encoding="utf-8")
    assert f"Musique : {music.title_of(Path(track))}, par Holizna, domaine public (CC0)" in text
    (library / "LICENCE.txt").unlink()
    assert f"Musique : {track}" in render.write_sources(job).read_text(encoding="utf-8")


def test_sources_md_has_no_music_line_without_music(job_with_voice_fixtures, home):
    from ideo import render

    job = job_with_voice_fixtures
    common.save_json(job / "info.json", {"id": "abcdefghijk", "duration": 120})
    write_config(home, {"music": False})
    assemble.assemble_part(job, 1)
    assert "Musique" not in render.write_sources(job).read_text(encoding="utf-8")
