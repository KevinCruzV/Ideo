import pytest

from ideo import countries, scene_schema


def test_about_eighty_countries_and_every_code_has_a_flag():
    assert len(countries.NAMES) >= 80
    assert set(countries.NAMES) <= set(scene_schema.FLAGS)


@pytest.mark.parametrize("label,code", [
    ("Chine", "cn"), ("china", "cn"), ("CHINE", "cn"), ("États-Unis", "us"), ("etats unis", "us"), ("USA", "us"),
    ("United States", "us"), ("Royaume-Uni", "gb"), ("royaume uni", "gb"), ("UK", "gb"), ("URSS", "su"),
    ("Union soviétique", "su"), ("Afrique du Sud", "za"), ("South Africa", "za"), ("Corée du Sud", "kr"),
    ("Corée du Nord", "kp"), ("Pays-Bas", "nl"), ("Russie", "ru"), ("Inde", "in"), ("Brésil", "br"),
    ("Union européenne", "eu"), ("ONU", "un"), ("Allemagne", "de"), ("Germany", "de"), ("Nouvelle-Zélande", "nz"),
    ("République démocratique du Congo", "cd"), ("Émirats arabes unis", "ae"),
])
def test_names_in_french_and_english_without_case_or_accents(label, code):
    assert countries.code_of(label) == code


@pytest.mark.parametrize("label", ["Chine du Sud", "La Chine", "Chine 18 %", "Paris", "", "Un", "Union", 3, None, "Inde et Chine"])
def test_only_exact_country_names_match(label):
    assert countries.code_of(label) is None


def test_no_two_countries_share_a_name():
    seen = {}
    for code, names in countries.NAMES.items():
        for name in names:
            key = countries.plain(name)
            assert seen.setdefault(key, code) == code, name
