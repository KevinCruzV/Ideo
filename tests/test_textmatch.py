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


def test_non_latin_scripts_match_themselves():
    assert textmatch.find_span(["Привет,", "мир", "снова"], "МИР снова") == (1, 2)
    assert textmatch.find_span(["مرحبا", "بالعالم"], "بالعالم") == (1, 1)
    assert textmatch.normalize("Привет") == "привет"


def test_ligatures_and_special_letters():
    assert textmatch.find_span(["une", "\u0153uvre", "d'art"], "oeuvre d'art") == (1, 2)
    assert textmatch.find_span(["la", "oeuvre"], "\u0153uvre") == (1, 1)
    assert textmatch.normalize("Stra\u00dfe") == "strasse"
    assert textmatch.normalize("\u0142\u00f3d\u017a") == "\u0142odz"


def test_hyphenated_words_split_consistently():
    assert textmatch.find_span(["Dis-moi", "pourquoi"], "moi") == (0, 0)
    assert textmatch.find_span(["Lui-m\u00eame", "le", "r\u00e9sume"], "lui m\u00eame le") == (0, 1)
    assert textmatch.find_span(["lui", "m\u00eame"], "Lui-m\u00eame") == (0, 1)
