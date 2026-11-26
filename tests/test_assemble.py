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
    assert starts[:4] == pytest.approx([0.0, 1.4, 2.9, 4.4], abs=0.05)
    assert starts[4:] == pytest.approx([8.4, 9.9, 15.92], abs=0.05)
    sfx = offsets[3]["clip"]
    assert sfx["kind"] == "sfx"
    assert sfx["start"] == pytest.approx(5.65, abs=0.05) and sfx["end"] - sfx["start"] == pytest.approx(2.5, abs=0.05)
    quote = offsets[5]["clip"]
    assert quote["kind"] == "quote"
    assert quote["start"] == pytest.approx(10.75, abs=0.05) and quote["end"] - quote["start"] == pytest.approx(4.92, abs=0.05)
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


def test_gaps_are_marked_by_position():
    assert (assemble.GAP_HOOK, assemble.GAP_SCENE, assemble.GAP_BREAK) == (0.60, 0.50, 0.90)


def test_break_scene_gets_the_long_pause(job_with_voice_fixtures):
    job = job_with_voice_fixtures
    plan = common.load_json(job / "plan.json")
    plan["parts"][0]["scenes"][1]["break"] = True
    common.save_json(job / "plan.json", plan)
    assemble.assemble_part(job, 1)
    offsets = common.load_json(job / "parts" / "01" / "offsets.json")
    assert offsets[2]["start"] - offsets[1]["end"] == pytest.approx(0.90, abs=0.01)
    assert offsets[1]["start"] - offsets[0]["end"] == pytest.approx(0.60, abs=0.01)
    assert offsets[3]["start"] - offsets[2]["end"] == pytest.approx(0.50, abs=0.01)


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


def _breathy_segment(path, words_path):
    import numpy as np

    rate = 48000
    rng = np.random.default_rng(2)
    t = np.arange(rate)
    tone = (8000 * np.sin(2 * np.pi * 440 * t / rate)).astype(np.int16)
    breath = (rng.standard_normal(int(0.5 * rate)) * 600).astype(np.int16)
    pcm = np.concatenate([breath, tone, breath, tone, breath])
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    common.save_json(words_path, [{"w": "un", "s": 0.5, "e": 1.5}, {"w": "deux", "s": 2.0, "e": 3.0}])
    return pcm


def test_paid_voice_breaths_are_muted_at_assembly_without_touching_the_segments(job_with_voice_fixtures):
    import numpy as np

    job = job_with_voice_fixtures
    out_dir = job / "parts" / "01"
    original = _breathy_segment(out_dir / "seg_01.wav", out_dir / "seg_01.words.json")
    before = (out_dir / "seg_01.wav").read_bytes()
    common.save_json(out_dir / "voice-info.json", {"engine": "elevenlabs"})
    pcm = np.frombuffer(assemble._voice_pcm(out_dir, "seg_01"), dtype="<i2")
    assert len(pcm) == len(original)
    assert np.max(np.abs(pcm[:int(0.4 * 48000)])) == 0
    assert np.max(np.abs(pcm[int(1.75 * 48000):int(1.9 * 48000)])) == 0
    assert np.max(np.abs(pcm[int(3.3 * 48000):])) == 0
    assert np.array_equal(pcm[int(0.6 * 48000):int(1.4 * 48000)], original[int(0.6 * 48000):int(1.4 * 48000)])
    assert (out_dir / "seg_01.wav").read_bytes() == before


def test_local_voice_segments_are_read_as_they_are(job_with_voice_fixtures):
    job = job_with_voice_fixtures
    out_dir = job / "parts" / "01"
    _breathy_segment(out_dir / "seg_01.wav", out_dir / "seg_01.words.json")
    common.save_json(out_dir / "voice-info.json", {"engine": "kyutai"})
    assert assemble._voice_pcm(out_dir, "seg_01") == (out_dir / "seg_01.wav").read_bytes()[44:]


def test_an_already_assembled_paid_part_is_reassembled_once_for_the_breath_gate(job_with_voice_fixtures):
    job = job_with_voice_fixtures
    out_dir = job / "parts" / "01"
    assemble.assemble_part(job, 1)
    common.save_json(out_dir / "voice-info.json", {"engine": "elevenlabs"})
    assert not assemble._music_current(job, out_dir)
    assemble.assemble_part(job, 1)
    assert assemble._music_current(job, out_dir)
    assert common.load_json(out_dir / "music.json")["breath_gate"] is True


def test_suspense_scene_gets_a_two_second_silence(job_with_voice_fixtures):
    job = job_with_voice_fixtures
    plan = common.load_json(job / "plan.json")
    plan["parts"][0]["scenes"][2]["suspense"] = True
    common.save_json(job / "plan.json", plan)
    assemble.assemble_part(job, 1)
    offsets = common.load_json(job / "parts" / "01" / "offsets.json")
    assert offsets[3]["start"] - offsets[2]["end"] == pytest.approx(assemble.GAP_SUSPENSE, abs=0.01)
