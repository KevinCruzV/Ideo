import numpy as np
import pytest

from ideo import sfx


def speech(start, end, step=0.3):
    out = []
    t = start
    while t < end:
        out.append({"w": "x", "s": round(t, 2), "e": round(t + 0.2, 2)})
        t += step
    return out


def make_rms(loud=None, n=30):
    rms = np.full(n, -50.0)
    if loud:
        rms[loud[0]:loud[1]] = -20.0
    return rms


def test_find_sfx_detects_loud_gap():
    words = speech(0, 10) + speech(13, 29)
    rms = make_rms((10, 13))
    found = sfx.find_sfx(rms, words)
    assert found[0]["at"] == "0:10"
    assert found[0]["s"] == 10.1 and found[0]["e"] == 13.0


def test_find_sfx_ignores_quiet_gap():
    words = speech(0, 10) + speech(13, 29)
    assert sfx.find_sfx(make_rms(), words) == []


def test_find_sfx_ignores_short_gap():
    words = speech(0, 10) + speech(10.5, 29)
    assert sfx.find_sfx(make_rms((10, 11)), words) == []


def test_find_sfx_ignores_loud_seconds_with_speech():
    words = speech(0, 29)
    assert sfx.find_sfx(make_rms((5, 9)), words) == []


def test_rms_db_per_second(tmp_path):
    import wave
    path = tmp_path / "a.wav"
    loud = (np.sin(np.arange(16000) / 5) * 16000).astype("<i2")
    quiet = (np.sin(np.arange(16000) / 5) * 16).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(np.concatenate([loud, quiet]).tobytes())
    db = sfx.rms_db_per_second(path)
    assert len(db) == 2 and db[0] - db[1] > 40


def test_find_sfx_keeps_one_sound_when_level_dips_slightly():
    words = speech(0, 10) + speech(40, 55)
    rms = make_rms(n=56)
    rms[10:30] = -20.0
    rms[14] = -45.0
    rms[19] = -45.0
    rms[23] = -45.0
    found = sfx.find_sfx(rms, words)
    assert len(found) == 1
    assert found[0]["s"] == 10.1 and found[0]["e"] - found[0]["s"] > 9


def test_find_sfx_bridges_a_one_second_pause():
    words = speech(0, 10) + speech(40, 55)
    rms = make_rms(n=56)
    rms[10:14] = -20.0
    rms[15:19] = -20.0
    found = sfx.find_sfx(rms, words)
    assert len(found) == 1
    assert found[0]["e"] == 19.0


def test_find_sfx_splits_after_a_long_pause():
    words = speech(0, 10) + speech(40, 55)
    rms = make_rms(n=56)
    rms[10:14] = -20.0
    rms[20:24] = -20.0
    assert len(sfx.find_sfx(rms, words)) == 2


def test_find_sfx_ignores_a_run_that_is_never_loud_enough():
    words = speech(0, 10) + speech(40, 55)
    rms = make_rms(n=56)
    rms[10:20] = -45.0
    assert sfx.find_sfx(rms, words) == []


def test_find_sfx_caps_the_length_of_one_sound():
    words = speech(0, 10) + speech(60, 75)
    rms = make_rms(n=200)
    rms[10:60] = -20.0
    found = sfx.find_sfx(rms, words)
    assert len(found) == 1
    assert found[0]["e"] - found[0]["s"] == pytest.approx(sfx.MAX_SFX)
