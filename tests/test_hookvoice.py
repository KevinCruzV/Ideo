import pytest

from ideo import align, hookvoice


@pytest.mark.parametrize("text,lang,expected", [
    ("Dis-moi qui domine vraiment le monde ?", "fr", "Dis-moi ?! Qui domine vraiment le monde ?!"),
    ("Dis-moi pourquoi ta position de sommeil change tout ?", "fr", "Dis-moi ?! Pourquoi ta position de sommeil change tout ?!"),
    ("Dis-moi, pourquoi tu oublies ?", "fr", "Dis-moi ?! Pourquoi tu oublies ?!"),
    ("dis-moi pourquoi tu oublies?", "fr", "dis-moi ?! Pourquoi tu oublies?!"),
    ("Dis-moi comment on dort.", "fr", "Dis-moi ?! Comment on dort!"),
    ("Tell me who rules the world?", "en", "Tell me ?! Who rules the world?!"),
    ("Sag mir, wer regiert die Welt?", "de", "Sag mir ?! Wer regiert die Welt?!"),
    ("Dime quién manda ?", "es", "Dime ?! Quién manda ?!"),
])
def test_tell_me_hooks_are_split_into_two_questions(text, lang, expected):
    assert hookvoice.shape(text, lang) == expected


@pytest.mark.parametrize("text,expected", [
    ("Et si le monde changeait ?", "Et si le monde changeait ?!"),
    ("Tu sais ce qui se passe ?", "Tu sais ce qui se passe ?!"),
    ("Pourquoi tu oublies ?", "Pourquoi tu oublies ?!"),
    ("Voici comment tout a changé.", "Voici comment tout a changé!"),
    ("Quel monde !", "Quel monde !"),
    ("Qui domine ?!", "Qui domine ?!"),
    ("Qui domine ??", "Qui domine ?!"),
    ("Sans ponctuation", "Sans ponctuation"),
    ("Imagine un monde sans fin...", "Imagine un monde sans fin!"),
])
def test_other_hooks_only_get_their_closing_mark_changed(text, expected):
    assert hookvoice.shape(text, "fr") == expected


def test_no_split_for_the_other_openers():
    assert "?!" not in hookvoice.shape("Tu sais ce qui se passe ?", "fr").replace("passe ?!", "")


def test_formula_alone_or_unknown_language_is_not_split():
    assert hookvoice.shape("Dis-moi", "fr") == "Dis-moi"
    assert hookvoice.shape("Dis-moi ?", "fr") == "Dis-moi ?!"
    assert hookvoice.shape("Dis-moi qui ?", "pt") == "Dis-moi qui ?!"


def test_word_count_is_preserved_so_alignment_stays_right():
    for text in ["Dis-moi qui domine vraiment le monde ?", "Pourquoi tu oublies ?", "Tell me why it works."]:
        for lang in ("fr", "en"):
            assert len(align.script_words(hookvoice.shape(text, lang))) == len(align.script_words(text))


import numpy as np

from ideo import hookvoice as hv


def test_syllable_heuristic_for_french_and_english():
    assert [hv.syllables(w) for w in ("vraiment", "monde", "domine", "qui", "changement", "world", "the")] == [2, 1, 2, 1, 3, 1, 1]
    assert hv.syllables("?!") == 1


def words(*items):
    return [{"w": w, "s": s, "e": e} for w, s, e in items]


def test_speed_ratio_compares_the_last_two_words_with_the_rest():
    even = words(("qui", 0.0, 0.3), ("domine", 0.3, 0.8), ("vraiment", 0.8, 1.3), ("le", 1.3, 1.6), ("monde", 1.6, 1.8))
    assert 0.8 < hv.speed_ratio(even, 0) < 1.5
    dragging = words(("qui", 0.0, 0.3), ("domine", 0.3, 0.8), ("vraiment", 0.8, 1.3), ("le", 1.3, 2.0), ("monde", 2.0, 3.5))
    assert hv.speed_ratio(dragging, 0) < hv.SPEED_RATIO_MIN


def test_speed_ratio_skips_the_formula_and_needs_enough_words():
    sample = words(("Dis-moi", 0.0, 0.5), ("qui", 0.5, 0.8), ("domine", 0.8, 1.3), ("le", 1.3, 1.5), ("monde", 1.5, 2.0))
    assert hv.speed_ratio(sample, 1) is not None
    assert hv.speed_ratio(sample[:3], 1) is None


def test_failed_criteria_and_unknowns():
    assert hv.failed({"fidelity": 1.0, "formula": None, "speed_ratio": None}) == []
    assert hv.failed({"fidelity": 0.89, "formula": 0.51, "speed_ratio": 0.84}) == ["fidélité", "formule trop longue", "fin traînante"]
    assert hv.failed({"fidelity": 0.90, "formula": 0.50, "speed_ratio": 0.85}) == []


def test_failed_flags_a_final_rise_outside_the_target():
    assert hv.failed({"fidelity": 1.0, "formula": None, "speed_ratio": None, "rise": 8.0}) == []
    assert hv.failed({"fidelity": 1.0, "formula": None, "speed_ratio": None, "rise": 7.0}) == []
    assert hv.failed({"fidelity": 1.0, "formula": None, "speed_ratio": None, "rise": 10.0}) == []
    assert hv.failed({"fidelity": 1.0, "formula": None, "speed_ratio": None, "rise": 2.0}) == ["montée hors cible"]
    assert hv.failed({"fidelity": 1.0, "formula": None, "speed_ratio": None, "rise": 11.4}) == ["montée hors cible"]
    assert hv.failed({"fidelity": 1.0, "formula": None, "speed_ratio": None, "rise": None}) == []


def test_distance_to_the_targets():
    assert hv.distance({"rise": 8.0, "level": 3.0}) == 0
    assert hv.distance({"rise": 7.0, "level": 5.0}) == 0 and hv.distance({"rise": 10.0, "level": 2.0}) == 0
    assert hv.distance({"rise": 6.5, "level": 1.5}) == 1.0
    assert hv.distance({"rise": 11.4, "level": 6.3}) == pytest.approx(2.7)
    assert hv.distance({"rise": None, "level": 3.0}) == hv.UNKNOWN_DISTANCE


def test_ranking_puts_the_eliminatory_criteria_first():
    near = {"fidelity": 1.0, "formula": 0.7, "speed_ratio": 1.0, "rise": 8.0, "level": 3.0}
    far = {"fidelity": 1.0, "formula": 0.4, "speed_ratio": 1.0, "rise": 1.0, "level": 0.0}
    assert hv.best([{"scores": near}, {"scores": far}]) == 1
    slightly_high = {"fidelity": 1.0, "formula": 0.4, "speed_ratio": 1.0, "rise": 10.5, "level": 3.0}
    assert hv.best([{"scores": near}, {"scores": slightly_high}]) == 1
    both = {"fidelity": 1.0, "formula": 0.4, "speed_ratio": 1.0, "rise": 8.0, "level": 3.0}
    assert hv.best([{"scores": far}, {"scores": both}]) == 1
    assert hv.best([{"scores": both}, {"scores": dict(both)}]) == 0


def voiced(seconds, f0_of_t, rate=48000):
    t = np.arange(int(seconds * rate)) / rate
    phase = 2 * np.pi * np.cumsum(f0_of_t(t)) / rate
    wave = sum(np.sin(k * phase) / k for k in (1, 2, 3))
    return 0.3 * wave / np.max(np.abs(wave))


def test_contour_measures_the_internal_rise_and_the_final_level():
    def pitch(t):
        base = np.full_like(t, 120.0)
        ramp = np.clip((t - 1.0) / 0.9, 0, 1)
        return base * 2 ** (ramp * 8 / 12)

    signal = voiced(2.2, pitch)
    rise, level = hv.contour(signal, 48000, {"s": 1.0, "e": 2.0})
    assert 5.5 < rise < 9.5
    assert level > 2.0


def test_contour_flat_word_has_no_rise_and_unvoiced_has_none():
    flat = voiced(2.0, lambda t: np.full_like(t, 130.0))
    rise, level = hv.contour(flat, 48000, {"s": 1.0, "e": 1.9})
    assert abs(rise) < 1.0 and abs(level) < 1.5
    assert hv.contour(np.zeros(48000 * 2), 48000, {"s": 1.0, "e": 1.9}) == (None, None)


def test_contour_extends_the_last_word_by_80_ms():
    assert hv.LAST_WORD_TAIL == 0.08 and hv.RISE_TARGET == (7.0, 10.0) and hv.LEVEL_TARGET == (2.0, 5.0)
    assert (hv.FIDELITY_MIN, hv.FORMULA_MAX, hv.SPEED_RATIO_MIN, hv.TAKES) == (0.90, 0.50, 0.85, 12)


def test_formula_detection_and_length():
    assert hv.formula_length("fr") == 1 and hv.formula_length("en") == 2 and hv.formula_length("pt") == 0
    assert hv.starts_with_formula("Dis-moi ?! Qui domine ?!", "fr")
    assert not hv.starts_with_formula("Pourquoi tu oublies ?!", "fr")
    assert not hv.starts_with_formula("Dis-moi ?", "fr")
