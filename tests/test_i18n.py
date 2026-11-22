from ideo import i18n


def test_outro_text_fr_and_fallback():
    assert i18n.t("outro_next", "fr", n=2, title="Le sommeil") == "Si ça t'a plu, abonne-toi pour la partie 2 : Le sommeil !"
    assert i18n.t("outro_last", "xx") == i18n.t("outro_last", "en")


def test_fr_and_en_strings():
    assert i18n.t("part_label", "fr") == "Partie"
    assert i18n.t("part_label", "en") == "Part"
    assert i18n.t("outro_next", "en", n=3, title="Sleep") == "If you liked it, follow for part 3: Sleep!"
    assert i18n.t("outro_last", "fr") == "Si ça t'a plu, abonne-toi pour la prochaine série !"
    assert i18n.t("outro_last", "en") == "If you liked it, follow for the next series!"


def test_outro_single_all_languages():
    assert i18n.t("outro_single", "fr") == "Si ça t'a plu, abonne-toi pour la prochaine !"
    assert i18n.t("outro_single", "en") == "If you liked it, follow for the next one!"
    assert i18n.t("outro_single", "xx") == i18n.t("outro_single", "en")
    for lang in ("es", "de", "it", "pt"):
        assert i18n.t("outro_single", lang) != i18n.t("outro_single", "en")


def test_translated_languages_differ_from_english():
    for lang in ("es", "de", "it", "pt"):
        for key in ("part_label", "outro_last"):
            assert i18n.t(key, lang) != i18n.t(key, "en")
        text = i18n.t("outro_next", lang, n=4, title="Titre")
        assert "4" in text and "Titre" in text and text != i18n.t("outro_next", "en", n=4, title="Titre")


def test_every_voiced_language_has_its_fixed_strings_or_english():
    from ideo import voice

    for lang in voice.EDGE_VOICES:
        for key in i18n.STRINGS["en"]:
            assert i18n.t(key, lang, n=2, title="T", names="A")


def test_missing_key_falls_back_to_english_per_key(monkeypatch):
    monkeypatch.setitem(i18n.STRINGS, "zz", {"part_label": "Zz"})
    assert i18n.t("part_label", "zz") == "Zz"
    assert i18n.t("outro_last", "zz") == i18n.t("outro_last", "en")


def test_new_languages_are_translated():
    for lang in ("nl", "pl", "tr"):
        text = i18n.t("outro_next", lang, n=4, title="Titre")
        assert "4" in text and "Titre" in text and text != i18n.t("outro_next", "en", n=4, title="Titre")


def test_voices_line_in_every_voiced_language():
    from ideo import voice

    assert i18n.t("voices_line", "fr", names="A, B") == "Voix citées : A, B"
    assert i18n.t("voices_line", "xx", names="A") == "Quoted voices: A"
    for lang in voice.EDGE_VOICES:
        assert i18n.t("voices_line", lang, names="Zed").count("Zed") == 1
        assert lang == "en" or i18n.t("voices_line", lang, names="Zed") != i18n.t("voices_line", "en", names="Zed")


def test_removed_languages_have_no_fixed_strings():
    assert set(i18n.STRINGS) == {"fr", "en", "es", "de", "it", "pt", "nl", "pl", "tr"}


def test_every_closing_line_is_enthusiastic_and_ends_with_an_exclamation_mark():
    for lang in i18n.STRINGS:
        for key in ("outro_single", "outro_next", "outro_last"):
            text = i18n.t(key, lang, n=2, title="Titre")
            assert text.endswith("!") and chr(0x2014) not in text
