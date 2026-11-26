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


def timed(text):
    return [{"w": w, "s": i * 0.1, "e": i * 0.1 + 0.08} for i, w in enumerate(text.split())]


def test_trailing_extra_words_are_counted_apart_from_the_words_to_keep():
    assert fidelity.keep_count("Il a gagné le prix.", timed("Il a gagné le prix. coup")) == 5
    assert fidelity.keep_count("Il a gagné le prix.", timed("Il a gagné le prix. tropique de")) == 5
    assert fidelity.keep_count("Il a gagné le prix.", timed("Il a gagné le prix.")) is None
    assert fidelity.keep_count("Il a gagné le prix.", timed("Il a tout gagné le prix.")) is None
    assert fidelity.keep_count("Il a gagné 3 prix.", timed("Il a gagné trois prix. coup")) == 5


def test_a_proper_name_heard_differently_is_not_a_misreading():
    text = "Hier, Leclerc et Aldi comparent le même panier de courses cette semaine."
    assert fidelity.similarity(text, heard("Hier Le clerc et Haldi comparent le même panier de courses cette semaine")) == 1.0
    assert fidelity.similarity(text, heard("Hier Leclerc et Audi comparent le même panier de courses cette semaine")) == 1.0
    assert fidelity.added(text, heard("Hier Le clerc et Haldi comparent le même panier de courses cette semaine")) == []


def test_a_name_run_together_or_split_is_matched():
    text = "Selon Jean Dujardin, le film marche."
    assert fidelity.similarity(text, heard("Selon Jean Du Jardin le film marche")) == 1.0
    assert fidelity.similarity("Il a vu Jean Dujardin.", heard("Il a vu Jean Dujardin")) == 1.0


def test_a_real_misreading_of_a_normal_word_still_counts():
    text = "Leclerc vend le même panier de courses chaque semaine."
    assert fidelity.similarity(text, heard("Leclerc vend le mode panier de cours chaque semaine")) < 1.0


def test_a_missing_name_still_counts():
    text = "Le panier de Leclerc coûte moins cher cette semaine."
    assert fidelity.similarity(text, heard("Le panier de coûte moins cher cette semaine")) < 1.0


def test_keep_count_follows_the_folded_names():
    text = "Hier Leclerc et Aldi comparent."
    words = heard("Hier Le clerc et Haldi comparent coup")
    assert fidelity.keep_count(text, words) == 6


def test_a_misread_first_word_of_a_sentence_still_counts():
    text = "Pourtant le panier coûte moins cher. Selon Leclerc le prix baisse."
    exact = fidelity.similarity(text, heard("Pourtant le panier coûte moins cher Selon Leclerc le prix baisse"))
    assert exact == 1.0
    assert fidelity.similarity(text, heard("Pourtan le panier coûte moins cher Selon Leclerc le prix baisse")) < exact
    assert fidelity.similarity(text, heard("Pourtant le panier coûte moins cher Celon Leclerc le prix baisse")) < exact


def test_a_word_heard_as_two_words_is_not_an_added_word():
    text = "Alors qui encaisse ? Au début de la chaîne, les producteurs de lait."
    words = heard("Alors qui en caisse Au début de la chaîne les producteurs de lait")
    assert fidelity.similarity(text, words) == 1.0
    assert fidelity.added(text, words) == []


def test_a_name_opening_the_text_heard_as_two_words_is_not_an_added_word():
    text = "Leclerc ou Aldi, qui vole le plus les Français ?"
    words = heard("Le claire ou Haldi qui vole le plus les Français")
    assert fidelity.similarity(text, words) == 1.0
    assert fidelity.added(text, words) == []


def test_a_word_split_into_unrelated_words_still_counts():
    text = "Alors qui encaisse ? Au début de la chaîne, les producteurs de lait."
    assert fidelity.similarity(text, heard("Alors qui en mange Au début de la chaîne les producteurs de lait")) < 1.0
    assert fidelity.added(text, heard("Alors qui en mange Au début de la chaîne les producteurs de lait")) != []


def test_keep_count_follows_the_split_words():
    assert fidelity.keep_count("Alors qui encaisse.", timed("Alors qui en caisse. coup")) == 4
