import numpy as np
import pytest

from ideo import pacing

RATE = 48000


def tone(seconds, amp=8000):
    t = np.arange(int(seconds * RATE))
    return (amp * np.sin(2 * np.pi * 440 * t / RATE)).astype(np.int16)


def quiet(seconds):
    return np.zeros(int(seconds * RATE), dtype=np.int16)


def test_leading_and_trailing_silence_are_trimmed_keeping_30_ms():
    pcm = np.concatenate([quiet(0.5), tone(1.0), quiet(0.8)])
    out, mapping = pacing.tighten(pcm)
    assert len(out) / RATE == pytest.approx(1.06, abs=0.015)
    assert mapping(0.5) == pytest.approx(0.03, abs=0.015)
    assert mapping(1.5) == pytest.approx(1.03, abs=0.015)


def test_long_inner_silence_becomes_500_ms():
    pcm = np.concatenate([tone(0.5), quiet(1.0), tone(0.5)])
    out, mapping = pacing.tighten(pcm)
    assert len(out) / RATE == pytest.approx(1.5, abs=0.03)
    assert mapping(1.5) == pytest.approx(0.5 + 0.50, abs=0.02)
    assert mapping(0.25) == pytest.approx(0.25, abs=0.01)


def test_short_inner_silence_is_kept():
    pcm = np.concatenate([tone(0.5), quiet(0.55), tone(0.5)])
    out, _ = pacing.tighten(pcm)
    assert len(out) == len(pcm)


def test_mapping_is_non_decreasing():
    pcm = np.concatenate([quiet(0.4), tone(0.5), quiet(1.2), tone(0.5), quiet(0.9)])
    _, mapping = pacing.tighten(pcm)
    values = [mapping(t / 100) for t in range(0, 360)]
    assert all(a <= b + 1e-9 for a, b in zip(values, values[1:]))


def test_all_silent_input_is_returned_unchanged():
    pcm = quiet(1.0)
    out, mapping = pacing.tighten(pcm)
    assert len(out) == len(pcm) and mapping(0.7) == pytest.approx(0.7)


def test_apply_maps_word_times():
    pcm = np.concatenate([quiet(0.5), tone(0.5), quiet(1.0), tone(0.5)])
    _, mapping = pacing.tighten(pcm)
    words = pacing.remap([{"w": "a", "s": 0.6, "e": 0.9}, {"w": "b", "s": 2.1, "e": 2.4}], mapping)
    assert words[0]["s"] == pytest.approx(0.13, abs=0.02)
    assert words[1]["s"] == pytest.approx(1.13, abs=0.05)


def words_of(*spans):
    return [{"w": w, "s": s, "e": e} for w, s, e in spans]


def test_a_sentence_end_followed_too_quickly_gets_a_pause():
    pcm = np.concatenate([tone(1.0), quiet(0.18), tone(1.0)])
    heard = words_of(("grippe.", 0.1, 1.0), ("Entre", 1.18, 1.6))
    out, mapping = pacing.pause_sentences(pcm, heard)
    assert len(out) / RATE == pytest.approx(len(pcm) / RATE + (pacing.SENTENCE_GAP - 0.18), abs=0.01)
    assert mapping(1.0) == pytest.approx(1.0, abs=0.01)
    assert mapping(1.18) == pytest.approx(1.18 + (pacing.SENTENCE_GAP - 0.18), abs=0.01)
    inserted = out[int(1.0 * RATE) + 4800:int((1.18 + 0.1) * RATE)]
    assert np.max(np.abs(inserted)) == 0


def test_commas_long_gaps_and_the_last_word_are_left_alone():
    pcm = np.concatenate([tone(1.0), quiet(0.18), tone(1.0), quiet(0.5), tone(0.5)])
    heard = words_of(("Chine,", 0.1, 1.0), ("alors", 1.18, 2.1), ("nord.", 2.1, 2.2), ("Europe", 2.7, 3.2))
    out, mapping = pacing.pause_sentences(pcm, heard)
    assert len(out) == len(pcm) and mapping(2.0) == 2.0
    out, _ = pacing.pause_sentences(pcm, words_of(("fin.", 0.1, 1.0)))
    assert len(out) == len(pcm)


def test_an_abbreviation_is_not_a_sentence_end():
    pcm = np.concatenate([tone(1.0), quiet(0.05), tone(1.0)])
    out, _ = pacing.pause_sentences(pcm, words_of(("M.", 0.1, 1.0), ("Dupont", 1.05, 1.6)))
    assert len(out) == len(pcm)


def test_the_soft_tail_of_the_last_word_is_kept():
    pcm = np.concatenate([quiet(0.3), tone(1.0), tone(0.3, 400), quiet(0.8)])
    out, mapping = pacing.tighten(pcm)
    assert len(out) / RATE >= 1.0 + 0.3 * 0.9
    assert mapping(1.6) == pytest.approx(1.33, abs=0.02)


def test_the_soft_start_of_the_first_word_is_kept():
    pcm = np.concatenate([quiet(0.5), tone(0.2, 400), tone(1.0), quiet(0.5)])
    out, _ = pacing.tighten(pcm)
    assert len(out) / RATE >= 1.2 * 0.9
