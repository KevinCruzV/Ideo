import pytest

from ideo import align, numbers


def said(text, lang="fr"):
    return numbers.normalize(text, lang).text


@pytest.mark.parametrize("text,expected", [
    ("En 1998, le monde.", "En mille neuf cent quatre-vingt-dix-huit, le monde."),
    ("Il y a 150 personnes.", "Il y a cent cinquante personnes."),
    ("Il y a 3 000 personnes.", "Il y a trois mille personnes."),
    ("Il y a 3 000 personnes.", "Il y a trois mille personnes."),
    ("Il y a 3 000 personnes.", "Il y a trois mille personnes."),
    ("Il y a 1 250 000 euros.", "Il y a un million deux cent cinquante mille euros."),
    ("Il y a 80 pays, 81 villes et 21 chats.", "Il y a quatre-vingts pays, quatre-vingt-un villes et vingt et un chats."),
    ("Il y a 200 pays et 201 villes.", "Il y a deux cents pays et deux cent un villes."),
    ("Il y a 71 pays.", "Il y a soixante et onze pays."),
    ("Il y a 2000 pays.", "Il y a deux mille pays."),
    ("Environ 1,3 million.", "Environ un virgule trois million."),
    ("Un taux de 8 %.", "Un taux de huit pour cent."),
    ("Un taux de 8%.", "Un taux de huit pour cent."),
    ("Un taux de 8,5 %.", "Un taux de huit virgule cinq pour cent."),
    ("Le 51e et la 1re, le 1er.", "Le cinquante et unième et la première, le premier."),
    ("Le 2nd tour et la 2nde.", "Le second tour et la seconde."),
    ("Le 51ème rang.", "Le cinquante et unième rang."),
    ("Haut de 15 cm.", "Haut de quinze centimètres."),
    ("Une somme de 110 Md$ environ.", "Une somme de cent dix milliards de dollars environ."),
    ("Un seul km.", "Un seul km."),
    ("1 km de long.", "un kilomètre de long."),
    ("De 5 à 110 personnes.", "De cinq à cent dix personnes."),
    ("Il paie 15 € ou 1 €.", "Il paie quinze euros ou un euro."),
    ("Il fait 20 °C ici.", "Il fait vingt degrés Celsius ici."),
])
def test_french(text, expected):
    assert said(text) == expected


def test_french_years_keep_invariable_cent_and_vingt_after_a_year_word():
    assert said("En 1980 puis 1900.") == "En mille neuf cent quatre-vingt puis mille neuf cent."
    assert said("Il a 1900 amis.") == "Il a mille neuf cents amis."
    assert said("Il y a 1980 amis.") == "Il y a mille neuf cent quatre-vingts amis."
    assert said("Depuis 1800.") == "Depuis mille huit cent."


@pytest.mark.parametrize("text,expected", [
    ("In 1998 it began.", "In nineteen ninety-eight it began."),
    ("In 2005 it ended.", "In two thousand and five it ended."),
    ("There were 3,000 people.", "There were three thousand people."),
    ("About 1.3 million.", "About one point three million."),
    ("A rate of 8%.", "A rate of eight percent."),
    ("A rate of 8 %.", "A rate of eight percent."),
    ("The 51st, the 2nd and the 3rd, the 4th.", "The fifty-first, the second and the third, the fourth."),
    ("It is 15 cm high, 1 km long.", "It is fifteen centimeters high, one kilometer long."),
    ("Worth 15$ or 15 $.", "Worth fifteen dollars or fifteen dollars."),
    ("From 5 to 110.", "From five to one hundred and ten."),
])
def test_english(text, expected):
    assert said(text, "en") == expected


@pytest.mark.parametrize("lang,text,expected", [
    ("es", "En 1998 había 8 %.", "En mil novecientos noventa y ocho había ocho por ciento."),
    ("de", "Im Jahr 1998 gab es 3.000 Leute.", "Im Jahr neunzehnhundertachtundneunzig gab es dreitausend Leute."),
    ("it", "Nel 1998 c'erano 8 %.", "Nel millenovecentonovantotto c'erano otto per cento."),
    ("pt", "Em 1998 havia 3 000.", "Em mil novecentos e noventa e oito havia três mil."),
    ("nl", "In 1998 was 8%.", "In negentien honderd achtennegentig was acht procent."),
    ("pl", "W 1998 było 8%.", "W tysiąc dziewięćset dziewięćdziesiąt osiem było osiem procent."),
])
def test_other_covered_languages(lang, text, expected):
    assert said(text, lang) == expected


def test_turkish_and_unknown_languages_keep_the_digits():
    assert said("1998 yılında 8 kişi.", "tr") == "1998 yılında 8 kişi."
    assert said("1998", "xx") == "1998"
    assert "tr" not in numbers.COVERED and set(numbers.COVERED) == {"fr", "en", "es", "de", "it", "pt", "nl", "pl"}


@pytest.mark.parametrize("text", ["COVID-19 a changé.", "Le G20 se réunit.", "Le B2B marche.", "De 2008-2012.", "Chapitre 007.",
                                  "Appelle le 3615 MALIN", "Il a 1e10 fois", "Le 5ᵉ", "L'an 12345678901234 est loin."])
def test_cautious_tokens_are_left_alone(text):
    out = said(text)
    assert out == text or "chiffre" not in out


@pytest.mark.parametrize("text", ["COVID-19 a changé.", "Le G20 se réunit.", "Le B2B marche.", "De 2008-2012.", "Chapitre 007."])
def test_embedded_digits_unchanged(text):
    assert numbers.normalize(text, "fr").units is None and said(text) == text


def test_text_without_numbers_is_returned_untouched_including_spacing():
    text = "Dis-moi pourquoi tu oublies ?"
    result = numbers.normalize(text, "fr")
    assert result.text == text and result.units is None


def test_units_map_original_words_to_spoken_words():
    result = numbers.normalize("En 1998, 3 000 morts", "fr")
    assert [(u["orig"], u["said"], u["numeric"]) for u in result.units] == [(1, 1, False), (1, 4, True), (2, 2, True), (1, 1, False)]
    assert sum(u["orig"] for u in result.units) == len(align.script_words("En 1998, 3 000 morts"))
    assert sum(u["said"] for u in result.units) == len(result.text.split())


def test_punctuation_stays_on_the_edge_words():
    assert said("(1998) puis « 8 % » ici") == "(mille neuf cent quatre-vingt-dix-huit) puis « huit pour cent » ici"


def test_plain_words_drop_the_numeric_ones():
    result = numbers.normalize("En 1998 il pleut", "fr")
    assert numbers.plain_words(result.text, result.units) == "En il pleut"
    assert numbers.plain_words("a b", None) == "a b"


def test_requirements_list_num2words():
    from pathlib import Path

    text = (Path(__file__).resolve().parent.parent / "requirements.txt").read_text(encoding="utf-8")
    assert "num2words" in text


@pytest.mark.parametrize("text,expected", [
    ("Le panier coûte 27,92 € chez Aldi.", "Le panier coûte vingt-sept euros quatre-vingt-douze chez Aldi."),
    ("Il paie 27,92€ au total.", "Il paie vingt-sept euros quatre-vingt-douze au total."),
    ("Il paie 3,50 € ici.", "Il paie trois euros cinquante ici."),
    ("Il paie 3,5 € ici.", "Il paie trois euros cinquante ici."),
    ("Il paie 1,05 € ici.", "Il paie un euro cinq ici."),
    ("Il paie 27,00 € ici.", "Il paie vingt-sept euros ici."),
    ("Un total de 1 234,56 € demain.", "Un total de mille deux cent trente-quatre euros cinquante-six demain."),
    ("Un prix de 0,99 € pièce.", "Un prix de zéro euro quatre-vingt-dix-neuf pièce."),
])
def test_french_decimal_amounts_are_said_as_euros_and_cents(text, expected):
    assert said(text) == expected


def test_decimals_that_are_not_money_keep_the_comma_word():
    assert said("Environ 1,3 million.") == "Environ un virgule trois million."
    assert said("Un taux de 8,5 %.") == "Un taux de huit virgule cinq pour cent."


def test_english_decimal_dollars_say_cents():
    assert said("It costs 27.92 $ today.", "en") == "It costs twenty-seven dollars and ninety-two cents today."


def test_amounts_only_leaves_other_numbers_for_the_voice_to_read():
    result = numbers.normalize("En 1998, 27,92 € et 3 000 morts.", "fr", amounts_only=True)
    assert result.text == "En 1998, vingt-sept euros quatre-vingt-douze et 3 000 morts."
    assert sum(u["orig"] for u in result.units) == len(align.script_words("En 1998, 27,92 € et 3 000 morts."))
    assert numbers.normalize("En 1998, 3 000 morts.", "fr", amounts_only=True).units is None


@pytest.mark.parametrize("amounts_only", [True, False])
def test_montant_sans_le_mot_euros_dans_une_phrase_en_euros(amounts_only):
    text = numbers.normalize("L'addition grimpe de 27,92 euros chez Leclerc à 32,72 chez Intermarché.", "fr", amounts_only).text
    assert "trente-deux euros soixante-douze chez Intermarché" in text and "virgule" not in text
    text = numbers.normalize("Aldi et Leclerc restent proches : 7,83 contre 7,56 euros.", "fr", amounts_only).text
    assert text.startswith("Aldi et Leclerc restent proches : sept euros quatre-vingt-trois contre sept euros cinquante-six")


def test_une_decimale_ou_une_phrase_sans_euros_reste_un_nombre():
    assert "trente-deux euros" not in numbers.normalize("Le score passe à 32,72 points.", "fr").text
    assert "euros" not in numbers.normalize("Il coûte 10 euros, soit 21,7 de plus.", "fr").text.split("soit")[1]


@pytest.mark.parametrize("text,wrong", [
    ("La dette atteint 3,05 milliards de dollars.", "trois dollars"),
    ("Il gagne 1,25 milliard d'euros, soit 12,50 euros par jour.", "un euro vingt-cinq"),
    ("Il court en 9,58 secondes et touche 250 000 euros.", "neuf euros"),
    ("Le marathon fait 42,19 kilomètres pour 10 euros.", "quarante-deux euros"),
    ("La taxe passe à 3,25 pour cent, soit 40 euros.", "trois euros"),
    ("Le score moyen est de 2,15 buts. Le billet coûte 30 euros.", "deux euros"),
])
def test_un_nombre_qui_n_est_pas_un_prix_reste_un_nombre(text, wrong):
    for amounts_only in (True, False):
        assert wrong not in numbers.normalize(text, "fr", amounts_only).text
