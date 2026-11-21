import wave

import pytest

from ideo import assemble, common

DURATIONS = [0.8, 1.0, 1.0, 1.0, 1.0, 0.6, 0.8]
NAMES = ["seg_00_hook", "seg_01", "seg_02", "seg_03", "seg_04", "seg_05", "seg_99_outro"]


def wav_info(path):
    with wave.open(str(path), "rb") as w:
        return w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes() / w.getframerate()


def test_quote_bounds_use_margin_and_first_last_word():
    words = [{"w": "avant", "s": 24.0, "e": 24.5}, {"w": "Nous", "s": 26.4, "e": 26.7},
             {"w": "oublions,", "s": 26.76, "e": 27.0}, {"w": "tout.", "s": 27.1, "e": 27.5}]
    start, end = assemble.quote_bounds(words, "nous oublions tout", "0:26", duration=100.0)
    assert start == pytest.approx(26.25) and end == pytest.approx(27.65)


def test_quote_bounds_clamped_to_file():
    words = [{"w": "Nous", "s": 0.05, "e": 0.3}, {"w": "oublions", "s": 0.4, "e": 0.9}]
    start, end = assemble.quote_bounds(words, "nous oublions", "0:00", duration=1.0)
    assert start == 0.0 and end == 1.0


def test_quote_bounds_ignores_occurrence_beyond_90_seconds():
    words = [{"w": "Nous", "s": 300.0, "e": 300.3}, {"w": "oublions", "s": 300.4, "e": 300.9}]
    with pytest.raises(common.IdeoError):
        assemble.quote_bounds(words, "nous oublions", "0:10", duration=400.0)


def test_assemble_inserts_quote_and_sfx_clips_and_writes_offsets(job_with_voice_fixtures):
    job = job_with_voice_fixtures
    out = assemble.assemble_part(job, 1)
    assert out == job / "parts" / "01" / "part.wav"
    rate, channels, width, total = wav_info(out)
    assert (rate, channels, width) == (48000, 1, 2)
    offsets = common.load_json(job / "parts" / "01" / "offsets.json")
    assert [o["seg"] for o in offsets] == NAMES
    for o, d in zip(offsets, DURATIONS):
        assert o["end"] - o["start"] == pytest.approx(d, abs=0.05)
    starts = [o["start"] for o in offsets]
    assert starts[:4] == pytest.approx([0.0, 1.08, 2.36, 3.64], abs=0.05)
    assert starts[4:] == pytest.approx([7.64, 8.92, 14.94], abs=0.05)
    sfx = offsets[3]["clip"]
    assert sfx["kind"] == "sfx"
    assert sfx["start"] == pytest.approx(4.89, abs=0.05) and sfx["end"] - sfx["start"] == pytest.approx(2.5, abs=0.05)
    quote = offsets[5]["clip"]
    assert quote["kind"] == "quote"
    assert quote["start"] == pytest.approx(9.77, abs=0.05) and quote["end"] - quote["start"] == pytest.approx(4.92, abs=0.05)
    assert [o["clip"] for i, o in enumerate(offsets) if i not in (3, 5)] == [None] * 5
    assert total == pytest.approx(offsets[-1]["end"], abs=0.05)


def test_assemble_is_idempotent_and_marks_status(job_with_voice_fixtures):
    job = job_with_voice_fixtures
    assemble.assemble_part(job, 1)
    first = (job / "parts" / "01" / "offsets.json").read_text(encoding="utf-8")
    assemble.assemble_part(job, 1)
    assert (job / "parts" / "01" / "offsets.json").read_text(encoding="utf-8") == first
    assert common.read_status(job)["steps"]["assemble-01"]["ok"] is True


def test_assemble_prefers_m4a_source(job_with_voice_fixtures, monkeypatch):
    job = job_with_voice_fixtures
    (job / "source.m4a").write_bytes(b"not audio")
    with pytest.raises(common.IdeoError):
        assemble.assemble_part(job, 1)
    assert common.read_status(job)["steps"]["assemble-01"]["ok"] is False


def test_assemble_missing_segment_is_french_error(job_with_voice_fixtures):
    job = job_with_voice_fixtures
    (job / "parts" / "01" / "seg_02.wav").unlink()
    with pytest.raises(common.IdeoError, match="seg_02"):
        assemble.assemble_part(job, 1)


def test_assemble_unknown_part(job_with_voice_fixtures):
    with pytest.raises(common.IdeoError, match="partie 7"):
        assemble.assemble_part(job_with_voice_fixtures, 7)


def test_assemble_quote_not_in_source_is_french_error(job_with_voice_fixtures):
    job = job_with_voice_fixtures
    plan = common.load_json(job / "plan.json")
    plan["parts"][0]["scenes"][-1]["props"]["text"] = "phrase inventée absente"
    common.save_json(job / "plan.json", plan)
    with pytest.raises(common.IdeoError, match="citation"):
        assemble.assemble_part(job, 1)


def measured_lufs(path):
    import re
    import subprocess

    out = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", out)[-1])


def test_assembled_part_reaches_minus_14_lufs(job_with_voice_fixtures):
    out = assemble.assemble_part(job_with_voice_fixtures, 1)
    assert measured_lufs(out) == pytest.approx(-14.0, abs=0.5)


def test_gap_between_segments_is_280_ms():
    assert assemble.SILENCE_GAP == 0.28


def test_reach_target_lifts_a_quiet_part_to_minus_14(tmp_path):
    from tests.conftest import write_sine_wav

    path = tmp_path / "p.wav"
    write_sine_wav(path, seconds=2.0)
    import subprocess

    quiet = tmp_path / "q.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-af", "volume=-22dB", str(quiet)], check=True)
    assert measured_lufs(quiet) < -30
    assemble.reach_target(quiet, tmp_path, tmp_path / "log")
    assert measured_lufs(quiet) == pytest.approx(-14.0, abs=0.5)
