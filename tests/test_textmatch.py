from ideo import textmatch


def test_find_span_is_accent_and_case_insensitive():
    assert textmatch.find_span(["Il", "a", "été", "créé"], "ete CREE") == (2, 3)


def test_find_span_ignores_punctuation_and_apostrophe_style():
    words = ["Voilà,", "l’oubli", "arrive."]
    assert textmatch.find_span(words, "l'oubli arrive") == (1, 2)


def test_find_span_respects_start_and_misses():
    words = ["a", "b", "a", "b"]
    assert textmatch.find_span(words, "a b", start=1) == (2, 3)
    assert textmatch.find_span(words, "b c") is None
    assert textmatch.find_span(words, "") is None


def test_normalize():
    assert textmatch.normalize("Été,") == "ete"
    assert textmatch.normalize("L’Oubli") == "l'oubli"


def test_closest_passage_returns_timestamp_and_text():
    words = [{"w": w, "s": float(i * 10), "e": i * 10 + 1.0} for i, w in enumerate("un deux trois quatre cinq six".split())]
    out = textmatch.closest_passage(words, "quatre cinq sept")
    assert out.startswith("[0:30] quatre cinq")
