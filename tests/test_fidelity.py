import pytest

from ideo import fidelity


def heard(text):
    return [{"w": w, "s": i * 0.3, "e": i * 0.3 + 0.2} for i, w in enumerate(text.split())]


def test_identical_text_is_one():
    text = "Le monde change vite autour de nous."
    assert fidelity.similarity(text, heard(text)) == 1.0


def test_case_accents_and_punctuation_are_ignored():
    assert fidelity.similarity("Été chaud, très chaud !", heard("ete chaud tres chaud")) == 1.0


def test_split_words_are_tolerated():
    assert fidelity.similarity("Les États-Unis et l'Union", heard("Les États -Unis et l 'Union")) == 1.0


def test_numbers_are_ignored_whether_digits_or_spelled_out():
    assert fidelity.similarity("En 1991 le bloc a disparu", heard("En mille neuf cent quatre-vingt-onze le bloc a disparu")) >= 0.9
    assert fidelity.similarity("Il a 20 ans de métier", heard("Il a vingt ans de métier")) >= 0.9
    assert fidelity.similarity("In 1991 the bloc fell", heard("In nineteen ninety one the bloc fell")) >= 0.9


def test_a_garbled_segment_scores_low():
    assert fidelity.similarity("Le monde change vite autour de nous aujourd'hui", heard("Le mode chante vide autour")) < 0.8


def test_missing_half_scores_about_half():
    text = "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima"
    assert 0.5 < fidelity.similarity(text, heard("alpha bravo charlie delta echo foxtrot")) < 0.75


def test_nothing_heard_is_zero_and_nothing_expected_is_one():
    assert fidelity.similarity("Un texte", []) == 0.0
    assert fidelity.similarity("1991", heard("mille neuf cent quatre-vingt-onze")) == 1.0


def test_extra_filler_words_cost_little():
    text = "Le monde change vite autour de nous"
    assert fidelity.similarity(text, heard("Le monde change vite autour de nous euh")) > 0.9


def test_best_of_picks_the_highest_score():
    assert fidelity.best([0.5, 0.95, 0.7]) == 1


def test_an_added_word_is_found_even_when_the_similarity_stays_high():
    expected = "Et la Chine, alors ? Ses empereurs préfèrent garder leur frontière nord. L'Europe, petite et divisée, va chercher au loin ce qui lui manque."
    heard = [{"w": expected.replace("préfèrent", "préfèrent tout")}]
    assert fidelity.similarity(expected, heard) > 0.95
    assert fidelity.added(expected, heard) == ["tout"]
    assert fidelity.added(expected, [{"w": expected}]) == []


def test_numbers_and_a_changed_word_are_not_added_words():
    assert fidelity.added("Il a 3 enfants", [{"w": "Il a trois enfants"}]) == []
    assert fidelity.added("Il a mangé le gâteau", [{"w": "Il a goûté le gâteau"}]) == []
    assert fidelity.added("Il a mangé", [{"w": "Il a vraiment très mangé"}]) == ["vraiment", "tres"]
