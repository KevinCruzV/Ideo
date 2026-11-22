import pytest

from ideo import codes


@pytest.mark.parametrize("message,code", [
    ("Partie 1, scène 1 : type inconnu « x ». Types possibles : a.", "type-inconnu"),
    ("Partie 1, scène 1 : prop inconnue « title » pour « key-title ». Props acceptées : text.", "props-invalides"),
    ("Partie 1, scène 1 : prop « text » manquante pour « key-title ». Props acceptées : text.", "props-invalides"),
    ("S : « props.to » doit être un nombre (sans guillemets ni unité).", "props-invalides"),
    ("S : « props.text » fait 95 caractères, 90 au plus à l'écran : raccourcis-le d'environ 1 mot, sinon le texte est coupé.", "texte-trop-long"),
    ("Partie 1, scène 2 : « el » « values.9 » invalide pour « shape-diagram ». Chemins acceptés : values.0.", "el-invalide"),
    ("S : « absent » n'est pas dans le texte de « say ». Recopie dans « on » un mot", "ancre-absente"),
    ("S : l'item « a » (« x ») est dit avant l'item « b » (« y »). Échange", "items-desordre"),
    ("S : citation introuvable à ± 90 s de 0:26. Passage le plus proche", "citation-introuvable"),
    ("S : la citation dure 9 s, 8 s au plus.", "citation-trop-longue"),
    ("S : « src » 0:15 est dans un passage sponsorisé (0:14 à 0:20), choisis un autre passage.", "source-sponsorisee"),
    ("S : « src » 0:15 est dans la fin de la vidéo (remerciements, appel à s'abonner), ignorée (0:14 à 0:20), choisis un autre passage.", "source-fin-video"),
    ("S : « say » contient le nom de la chaîne YouTube (« X »). Reformule", "nom-de-chaine"),
    ("S : tiret cadratin interdit dans « x ». Remplace-le", "tiret-cadratin"),
    ("S : « src » est manquant. Recopie le « mm:ss »", "src-invalide"),
    ("S : le son 1:10 n'est pas dans sfx.json. Repères disponibles", "sfx-invalide"),
    ("Partie 1 : durée estimée 30 s, trop courte (minimum 45 s).", "plan-trop-court"),
    ("Partie 1 : durée estimée 400 s, trop longue (maximum 300 s).", "plan-trop-long"),
    ("Plan : le contenu tient en une seule vidéo (durée estimée totale 200 s).", "parties-fusionnables"),
    ("Partie 1 : 46 scènes, 45 au plus par vidéo. Retire", "trop-de-scenes"),
    ("Plan : « wishes » doit être une liste de 0 à 5 textes.", "wishes-invalides"),
    ("Plan : « mood » doit valoir \"dark\".", "mood-invalide"),
    ("Plan : version 2 non supportée.", "plan-invalide"),
])
def test_error_messages_get_a_stable_code(message, code):
    assert codes.error_code(message) == code


def test_every_lesson_is_short_french_text_without_em_dash():
    for code, text in codes.LESSONS.items():
        assert code == code.lower() and " " not in code
        assert 10 < len(text) <= 200 and chr(0x2014) not in text and text.endswith(".")


def test_code_only_codes_have_no_lesson():
    assert not codes.CODE_ONLY & set(codes.LESSONS)
    assert {"silence-long", "scene-figee", "volume", "video-duree-differente"} <= codes.CODE_ONLY


def test_count():
    assert codes.count(["a", "b", "a"]) == {"a": 2, "b": 1}
