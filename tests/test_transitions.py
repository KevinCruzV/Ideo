import json
from pathlib import Path

import numpy as np
import pytest

from ideo import assemble, common, config, music, transitions

RATE = 48000


def active_rms(sound):
    mask = np.abs(sound) > 0.1 * np.max(np.abs(sound))
    return float(np.sqrt(np.mean(sound[mask] ** 2)))


def test_four_distinct_deterministic_variants():
    first = transitions.variants()
    assert len(first) == 4
    transitions.variants.cache_clear()
    again = transitions.variants()
    assert all(np.array_equal(a, b) for a, b in zip(first, again))
    for i in range(4):
        for j in range(i + 1, 4):
            assert not np.allclose(first[i], first[j])


def test_each_variant_is_short_soft_and_calibrated():
    for sound in transitions.variants():
        assert sound.dtype == np.float32 and np.all(np.isfinite(sound))
        duration = len(sound) / RATE
        assert 0.3 <= duration <= 0.5
        assert abs(sound[0]) < 0.05 * np.max(np.abs(sound)) and abs(sound[-1]) < 0.05 * np.max(np.abs(sound))
        assert active_rms(sound) == pytest.approx(1.0, rel=0.01)
        peak_at = int(np.argmax(np.abs(sound))) / RATE
        assert 0.08 <= peak_at <= 0.3
        assert np.max(np.abs(sound)) < 8.0


def test_whoosh_sweeps_and_rustle_is_brighter():
    def centroid(sound, a, b):
        part = sound[int(a * RATE):int(b * RATE)]
        spectrum = np.abs(np.fft.rfft(part))
        freqs = np.fft.rfftfreq(len(part), 1 / RATE)
        return float((spectrum * freqs).sum() / spectrum.sum())

    up, rustle, down = transitions.variants()[0], transitions.variants()[1], transitions.variants()[2]
    assert centroid(up, 0.05, 0.15) < centroid(up, 0.25, 0.4)
    assert centroid(down, 0.05, 0.15) > centroid(down, 0.25, 0.4)
    assert centroid(rustle, 0.0, 0.4) > centroid(up, 0.0, 0.4)


def test_the_timing_constants_are_the_ones_of_the_render():
    source = (common.REPO_ROOT / "render" / "src" / "chrome" / "Wipe.tsx").read_text(encoding="utf-8")
    import re

    before = int(re.search(r"WIPE_BEFORE = (\d+)", source).group(1))
    after = int(re.search(r"WIPE_AFTER = (\d+)", source).group(1))
    assert transitions.WIPE_BEFORE == before and transitions.WIPE_FRAMES == before + after
    shorts = (common.REPO_ROOT / "render" / "src" / "Short.tsx").read_text(encoding="utf-8")
    assert "from={segment.from - WIPE_BEFORE}" in shorts and "timeline.segments.slice(1)" in shorts
    assert transitions.FPS == 30


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    return tmp_path / "home"


def make_raw(tmp_path, seconds, spans):
    t = np.arange(int(seconds * RATE)) / RATE
    samples = np.zeros(len(t), dtype=np.float32)
    for start, end in spans:
        a, b = int(start * RATE), int(end * RATE)
        samples[a:b] = 0.2 * np.sin(2 * np.pi * 180 * t[a:b]) + 0.1 * np.sin(2 * np.pi * 520 * t[a:b])
    path = tmp_path / "raw.wav"
    music.write_wav(path, samples)
    return path


def offsets_of(spans, clips=None):
    clips = clips or {}
    return [{"start": s, "end": e, "clip": clips.get(i)} for i, (s, e) in enumerate(spans)]


def burst_energy(path, a, b):
    samples = music.read_wav(path)
    return float(np.sqrt(np.mean(samples[int(a * RATE):int(b * RATE)] ** 2)))


def test_sounds_start_seven_frames_before_each_boundary_and_never_before_the_first_or_after_the_last(tmp_path):
    spans = [(0.0, 2.0), (2.6, 5.0), (5.6, 8.0)]
    raw = make_raw(tmp_path, 9.0, spans)
    info = transitions.mix(raw, offsets_of(spans))
    assert info["count"] == 2 and info["skipped"] == 0
    first = round(round(2.6 * 30, 6)) - 7
    second = round(round(5.6 * 30, 6)) - 7
    for frame in (first, second):
        begin = frame / 30
        assert burst_energy(raw, begin, begin + 0.3) > 1e-3
    assert burst_energy(raw, 8.1, 9.0) < 1e-6


def test_nothing_before_the_first_frame_and_nothing_after_the_closing_sentence(tmp_path):
    spans = [(0.0, 2.0), (2.6, 5.0)]
    raw = make_raw(tmp_path, 8.0, spans)
    transitions.mix(raw, offsets_of(spans))
    samples = music.read_wav(raw)
    assert np.max(np.abs(samples[int(5.05 * RATE):])) < 1e-6
    assert np.max(np.abs(samples[int(2.05 * RATE):int((2.6 - 0.26) * RATE)])) < 1e-6


def test_sound_level_is_about_12_db_under_the_voice(tmp_path):
    spans = [(0.0, 2.0), (2.6, 5.0), (5.6, 8.0), (8.6, 11.0)]
    raw = make_raw(tmp_path, 12.0, spans)
    voice_rms = burst_energy(raw, 0.0, 2.0)
    info = transitions.mix(raw, offsets_of(spans))
    assert info["mean_db"] == pytest.approx(-12.0, abs=0.5)
    samples = music.read_wav(raw)
    begin = (round(round(2.6 * 30, 6)) - 7) / 30
    burst = samples[int(begin * RATE):int(2.6 * RATE) - 100]
    active = burst[np.abs(burst) > 0.1 * np.max(np.abs(burst))]
    measured = 20 * np.log10(float(np.sqrt(np.mean(active ** 2))) / voice_rms)
    assert -15.0 < measured < -9.0


def test_a_transition_over_a_source_clip_is_skipped(tmp_path):
    spans = [(0.0, 2.0), (5.7, 8.0), (8.6, 10.0)]
    raw = make_raw(tmp_path, 11.0, spans)
    offsets = offsets_of(spans)
    offsets[0]["clip"] = {"start": 5.4, "end": 5.65}
    info = transitions.mix(raw, offsets)
    assert info["skipped"] == 1 and info["count"] == 1


def test_a_transition_in_the_middle_of_a_phrase_is_6_db_lower(tmp_path):
    clean = [(0.0, 2.0), (2.6, 5.0), (5.6, 8.0)]
    overlapping = [(0.0, 2.0), (2.1, 5.0), (5.6, 8.0)]
    raw_a, raw_b = make_raw(tmp_path, 9.0, clean), make_raw(tmp_path, 9.0, overlapping)
    a = transitions.mix(raw_a, offsets_of(clean))
    info = transitions.mix(raw_b, offsets_of(overlapping))
    assert info["ducked"] == 1 and a["ducked"] == 0
    assert info["mean_db"] < a["mean_db"]
    assert info["mean_db"] == pytest.approx((-12 + -18) / 2, abs=0.6)


def test_variants_alternate_from_one_transition_to_the_next(tmp_path):
    spans = [(0.0, 1.0), (1.6, 2.6), (3.2, 4.2), (4.8, 5.8)]
    raw = make_raw(tmp_path, 7.0, spans)
    transitions.mix(raw, offsets_of(spans))
    samples = music.read_wav(raw)
    pieces = []
    for i in (1, 2, 3):
        begin = (round(round(spans[i][0] * 30, 6)) - 7) / 30
        pieces.append(samples[int(begin * RATE):int(begin * RATE) + 4000])
    assert not np.allclose(pieces[0], pieces[1]) and not np.allclose(pieces[1], pieces[2])


def test_disabled_or_single_segment_adds_nothing(tmp_path, home):
    spans = [(0.0, 2.0), (2.6, 5.0)]
    raw = make_raw(tmp_path, 6.0, spans)
    before = music.read_wav(raw).copy()
    (home / "config.json").write_text(json.dumps({"transition_sfx": False}), encoding="utf-8")
    assert transitions.mix(raw, offsets_of(spans))["count"] == 0
    assert np.array_equal(music.read_wav(raw), before)
    (home / "config.json").write_text("{}", encoding="utf-8")
    assert transitions.mix(raw, offsets_of(spans[:1]))["count"] == 0


def test_config_keys(home):
    assert config.transition_sfx_enabled() is True and config.transition_sfx_db() == -12
    (home / "config.json").write_text(json.dumps({"transition_sfx": False, "transition_sfx_db": -18}), encoding="utf-8")
    assert config.transition_sfx_enabled() is False and config.transition_sfx_db() == -18
    for bad in ({"transition_sfx": "oui"}, {"transition_sfx_db": 3}, {"transition_sfx_db": "x"}):
        (home / "config.json").write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(common.IdeoError, match="config.json"):
            config.transition_sfx_db()


def test_assembly_adds_the_transition_sounds_and_records_them(job_with_voice_fixtures):
    job = job_with_voice_fixtures
    out = assemble.assemble_part(job, 1)
    info = common.load_json(job / "parts" / "01" / "music.json")
    assert info["transitions"]["count"] >= 5 and info["transitions"]["enabled"] is True
    assert assemble._integrated(out) == pytest.approx(-14.0, abs=0.5)


def test_changing_the_transition_level_rebuilds_the_part(job_with_voice_fixtures, home):
    job = job_with_voice_fixtures
    assemble.assemble_part(job, 1)
    stamp = (job / "parts" / "01" / "part.wav").stat().st_mtime_ns
    assemble.assemble_part(job, 1)
    assert (job / "parts" / "01" / "part.wav").stat().st_mtime_ns == stamp
    (home / "config.json").write_text(json.dumps({"transition_sfx_db": -20}), encoding="utf-8")
    assemble.assemble_part(job, 1)
    assert (job / "parts" / "01" / "part.wav").stat().st_mtime_ns != stamp
