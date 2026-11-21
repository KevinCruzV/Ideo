import numpy as np
import pytest

from ideo import prosody

RATE = 48000


def voiced(seconds, f0_of_t):
    t = np.arange(int(seconds * RATE)) / RATE
    phase = 2 * np.pi * np.cumsum(f0_of_t(t)) / RATE
    wave = sum(np.sin(k * phase) / k for k in (1, 2, 3))
    return 0.3 * wave / np.max(np.abs(wave))


def test_constant_pitch_is_flat():
    signal = voiced(2.0, lambda t: np.full_like(t, 150.0))
    assert prosody.score_signal(signal, RATE) < 0.3


def test_pitch_movement_gives_a_higher_score():
    flat = prosody.score_signal(voiced(3.0, lambda t: np.full_like(t, 150.0)), RATE)
    mild = prosody.score_signal(voiced(3.0, lambda t: 150 * 2 ** (np.sin(2 * np.pi * 0.7 * t) * 1.0 / 12)), RATE)
    lively = prosody.score_signal(voiced(3.0, lambda t: 150 * 2 ** (np.sin(2 * np.pi * 0.7 * t) * 4.0 / 12)), RATE)
    assert flat < mild < lively


def test_score_is_in_semitones_around_the_median():
    amplitude = 3.0
    signal = voiced(4.0, lambda t: 150 * 2 ** (np.sin(2 * np.pi * 0.5 * t) * amplitude / 12))
    expected = amplitude / np.sqrt(2) * prosody.SCALE
    assert prosody.score_signal(signal, RATE) == pytest.approx(expected, rel=0.25)


def test_score_does_not_depend_on_the_register():
    low = prosody.score_signal(voiced(3.0, lambda t: 110 * 2 ** (np.sin(2 * np.pi * 0.7 * t) * 3.0 / 12)), RATE)
    high = prosody.score_signal(voiced(3.0, lambda t: 260 * 2 ** (np.sin(2 * np.pi * 0.7 * t) * 3.0 / 12)), RATE)
    assert low == pytest.approx(high, rel=0.2)


def test_silence_and_noise_have_no_score():
    assert prosody.score_signal(np.zeros(RATE * 2), RATE) is None
    rng = np.random.default_rng(1)
    noise = prosody.score_signal(0.2 * rng.standard_normal(RATE * 2), RATE)
    assert noise is None or noise > 0


def test_too_short_has_no_score():
    assert prosody.score_signal(np.zeros(100), RATE) is None


def test_score_reads_a_wav(tmp_path):
    from tests.conftest import write_sine_wav

    path = tmp_path / "a.wav"
    write_sine_wav(path, seconds=1.5)
    assert prosody.score(path) < 0.3


def test_median_ignores_missing_scores():
    assert prosody.median([1.0, None, 3.0, 2.0]) == 2.0
    assert prosody.median([None]) is None


def test_thresholds():
    assert prosody.FLAT == 2.0 and prosody.BOUNDARY == 2.4
