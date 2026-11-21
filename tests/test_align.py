import pytest

from ideo import align


def heard(*items):
    return [{"w": w, "s": s, "e": e} for w, s, e in items]


def test_script_words_split_on_spaces_and_keep_punctuation():
    assert align.script_words("Les États-Unis, c'est l'Union.") == ["Les", "États-Unis,", "c'est", "l'Union."]


def test_script_words_glue_lone_punctuation_to_previous_word():
    assert align.script_words("Dis-moi pourquoi ?") == ["Dis-moi", "pourquoi\u00a0?"]
    assert align.script_words("partie 2 : Le sommeil") == ["partie", "2\u00a0:", "Le", "sommeil"]


def test_script_words_glue_opening_marks_to_next_word():
    assert align.script_words("Il dit « non » hier") == ["Il", "dit", "«\u00a0non\u00a0»", "hier"]


def test_script_words_empty():
    assert align.script_words("   ") == []


def test_exact_words_keep_their_times():
    words = align.align_words(["Un", "deux", "trois."], heard(("Un", 0.1, 0.3), ("deux", 0.4, 0.6), ("trois", 0.7, 1.0)), 1.2)
    assert [w["w"] for w in words] == ["Un", "deux", "trois."]
    assert [(w["s"], w["e"]) for w in words] == [(0.1, 0.3), (0.4, 0.6), (0.7, 1.0)]


def test_split_recognition_matches_hyphen_and_apostrophe_words():
    script = ["Les", "États-Unis", "et", "l'Union"]
    recognised = heard(("Les", 0.0, 0.2), ("États", 0.3, 0.6), ("-Unis", 0.6, 0.9), ("et", 1.0, 1.1), ("l", 1.2, 1.3),
                       ("'Union", 1.3, 1.8))
    words = align.align_words(script, recognised, 2.0)
    assert [w["w"] for w in words] == script
    assert (words[1]["s"], words[1]["e"]) == (0.3, 0.9)
    assert (words[3]["s"], words[3]["e"]) == (1.2, 1.8)


def test_misrecognised_word_is_interpolated_between_neighbours():
    script = ["Un", "mot", "faux", "fin"]
    recognised = heard(("Un", 0.0, 0.4), ("mot", 0.5, 0.9), ("fo", 1.0, 1.2), ("fin", 2.0, 2.4))
    words = align.align_words(script, recognised, 2.5)
    assert words[2]["s"] >= words[1]["e"] - 1e-9 and words[2]["e"] <= words[3]["s"] + 1e-9
    assert words[2]["s"] < words[2]["e"]


def test_nothing_recognised_spreads_words_over_the_duration():
    words = align.align_words(["a", "bb", "cc", "d"], [], 2.0)
    assert words[0]["s"] == 0.0 and words[-1]["e"] <= 2.0
    assert all(a["s"] <= b["s"] for a, b in zip(words, words[1:]))
    assert all(w["e"] >= w["s"] for w in words)


def test_times_are_non_decreasing_and_inside_the_duration():
    script = ["a", "b", "c", "d", "e"]
    recognised = heard(("c", 0.5, 0.9), ("b", 0.2, 0.4), ("zz", 3.0, 3.5))
    words = align.align_words(script, recognised, 1.0)
    assert all(0.0 <= w["s"] <= w["e"] <= 1.0 for w in words)
    assert all(a["s"] <= b["s"] for a, b in zip(words, words[1:]))


def test_punctuation_only_script_word_still_gets_a_time():
    words = align.align_words(["Un", "-", "deux"], heard(("Un", 0.0, 0.2), ("deux", 0.5, 0.8)), 1.0)
    assert len(words) == 3 and words[1]["s"] <= words[2]["s"]


def test_empty_script_gives_no_words():
    assert align.align_words([], heard(("a", 0, 1)), 1.0) == []


def test_extra_recognised_words_are_ignored():
    words = align.align_words(["deux", "trois"], heard(("un", 0.0, 0.3), ("deux", 0.4, 0.6), ("trois", 0.7, 1.0),
                                                       ("quatre", 1.1, 1.4)), 1.5)
    assert [(w["s"], w["e"]) for w in words] == [(0.4, 0.6), (0.7, 1.0)]


def test_numbers_and_accents_are_normalised():
    words = align.align_words(["Été", "1991"], heard(("ete", 0.0, 0.3), ("1991", 0.4, 0.9)), 1.0)
    assert [(w["s"], w["e"]) for w in words] == [(0.0, 0.3), (0.4, 0.9)]


def test_french_high_punctuation_keeps_a_non_breaking_space():
    assert align.script_words("Tu vois tout ? Attention ! Ainsi : voilà ; fin") == [
        "Tu", "vois", "tout ?", "Attention !", "Ainsi :", "voilà ;", "fin"]
    assert align.script_words("Quoi ?! Non") == ["Quoi ?!", "Non"]


def test_glued_punctuation_is_left_alone():
    assert align.script_words("Tout? Attention! Ainsi: fin.") == ["Tout?", "Attention!", "Ainsi:", "fin."]
    assert align.script_words("Un - deux … trois") == ["Un-", "deux…", "trois"]


def test_spaced_punctuation_does_not_break_alignment_or_matching():
    words = align.script_words("Tu vois tout ? Oui")
    recognised = [{"w": "Tu", "s": 0.0, "e": 0.2}, {"w": "vois", "s": 0.3, "e": 0.6}, {"w": "tout", "s": 0.7, "e": 1.0},
                  {"w": "Oui", "s": 1.2, "e": 1.5}]
    aligned = align.align_words(words, recognised, 2.0)
    assert [w["w"] for w in aligned] == words and (aligned[2]["s"], aligned[2]["e"]) == (0.7, 1.0)
    from ideo import textmatch

    assert textmatch.find_span(words, "tout oui") == (2, 3)
    assert textmatch.find_span(words, "tout") == (2, 2)
