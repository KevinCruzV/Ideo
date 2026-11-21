from ideo import i18n


def test_outro_text_fr_and_fallback():
    assert i18n.t("outro_next", "fr", n=2, title="Le sommeil") == "Abonne-toi pour la partie 2 : Le sommeil"
    assert i18n.t("outro_last", "ja") == i18n.t("outro_last", "en")


def test_fr_and_en_strings():
    assert i18n.t("part_label", "fr") == "Partie"
    assert i18n.t("part_label", "en") == "Part"
    assert i18n.t("outro_next", "en", n=3, title="Sleep") == "Follow for part 3: Sleep"
    assert i18n.t("outro_last", "fr") == "Abonne-toi pour la prochaine série"
    assert i18n.t("outro_last", "en") == "Follow for the next series"


def test_outro_single_all_languages():
    assert i18n.t("outro_single", "fr") == "Abonne-toi pour la prochaine vid\u00e9o"
    assert i18n.t("outro_single", "en") == "Follow for the next video"
    assert i18n.t("outro_single", "ja") == i18n.t("outro_single", "en")
    for lang in ("es", "de", "it", "pt"):
        assert i18n.t("outro_single", lang) != i18n.t("outro_single", "en")


def test_translated_languages_differ_from_english():
    for lang in ("es", "de", "it", "pt"):
        for key in ("part_label", "outro_last"):
            assert i18n.t(key, lang) != i18n.t(key, "en")
        text = i18n.t("outro_next", lang, n=4, title="Titre")
        assert "4" in text and "Titre" in text and text != i18n.t("outro_next", "en", n=4, title="Titre")
