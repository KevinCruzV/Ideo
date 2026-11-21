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
