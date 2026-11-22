import pytest

from ideo import codes, review, slop


def part_of(*says, hook="Dis-moi pourquoi on oublie ?", props=None, kinds=None):
    scenes = []
    for i, say in enumerate(says):
        kind = (kinds or {}).get(i, "stamp")
        scene = {"type": kind, "say": say, "props": (props or {}).get(i, {"text": "T"}), "src": "0:10"}
        scenes.append(scene)
    return {"n": 1, "title": "Le sommeil", "hook": hook, "scenes": scenes}


def codes_in(part, lang="fr"):
    return [c for c, _, _, _ in slop.findings(part, 1, lang)]


def finding(part, code, lang="fr"):
    return next(f for f in slop.findings(part, 1, lang) if f[0] == code)


NEUTRAL = "Le sommeil dure environ huit heures chaque nuit pour la plupart des gens."


@pytest.mark.parametrize("text", [
    "Un test – avec demi-cadratin ici dans la phrase.", "Un test -- avec double trait ici dans la phrase.",
    "Un test - avec trait isolé ici dans la phrase.", "Un test \u2014 avec cadratin ici dans la phrase."])
def test_dashes(text):
    assert "ia-tiret" in codes_in(part_of(text))


@pytest.mark.parametrize("text", ["Les États-Unis et le quatre-vingt-dix-huit.", "Un peu-être, c'est-à-dire ceci.", "Le week-end, là-bas."])
def test_hyphenated_compounds_are_never_flagged(text):
    assert "ia-tiret" not in codes_in(part_of(text))


def test_dash_on_the_screen_and_in_the_hook():
    assert "ia-tiret" in codes_in(part_of(NEUTRAL, props={0: {"text": "Avant - après"}}))
    assert "ia-tiret" in codes_in(part_of(NEUTRAL, hook="Dis-moi – pourquoi ?"))


@pytest.mark.parametrize("word", ["révolutionnaire", "incroyable", "fascinante", "véritables", "crucial", "essentielle",
                                  "au cœur de la ville", "un monde où tout change", "une nouvelle ère", "changer la donne"])
def test_hollow_words_in_french(word):
    assert "ia-mots-creux" in codes_in(part_of(f"Cette idée est {word} pour tout le monde ici."))


def test_hollow_word_on_screen():
    assert "ia-mots-creux" in codes_in(part_of(NEUTRAL, props={0: {"text": "Une idée incroyable"}}))


@pytest.mark.parametrize("phrase", ["Plongeons dans le sujet", "Voyons ensemble comment ça marche", "Dans cette vidéo on parle de sommeil",
                                    "Tu vas voir que tout change"])
def test_announcements(phrase):
    assert "ia-annonce" in codes_in(part_of(phrase + " avec beaucoup de détails précis."))


@pytest.mark.parametrize("phrase", ["Honnêtement, ça surprend", "Soyons clairs, personne ne dort", "Spoiler : on dort mal", "Le truc, c'est que ça fatigue"])
def test_false_confidences(phrase):
    assert "ia-fausse-confidence" in codes_in(part_of(phrase + " tout le monde ici."))


@pytest.mark.parametrize("phrase", ["L'avenir nous le dira", "Une chose est sûre", "C'est à méditer", "Cela reste à voir"])
def test_vague_conclusions(phrase):
    assert "ia-conclusion-vague" in codes_in(part_of(phrase + " pour tout le monde ici."))


def test_binary_formula_only_from_the_second_use():
    once = part_of("Ce n'est pas un hasard, c'est une habitude ancienne et solide.", NEUTRAL)
    assert "ia-formule-binaire" not in codes_in(once)
    twice = part_of("Ce n'est pas un hasard, c'est une habitude ancienne et solide.", NEUTRAL,
                    "Non seulement on dort mal, mais on rêve moins aussi.")
    found = finding(twice, "ia-formule-binaire")
    assert "employée 2 fois" in found[2] and found[1] == "Partie 1, scène 1"


def test_three_short_sentences_in_a_row():
    short = part_of("Il dort. Il rêve. Il oublie. Puis le jour se lève sur la ville tranquille.")
    assert "ia-phrases-courtes" in codes_in(short)
    assert "Il dort. Il rêve. Il oublie." in finding(short, "ia-phrases-courtes")[2]
    assert "ia-phrases-courtes" not in codes_in(part_of("Il dort. Il rêve. Puis le jour se lève sur la ville tranquille."))
    assert "ia-phrases-courtes" not in codes_in(part_of("Il dort. Il rêve vraiment beaucoup. Il oublie."))


def test_short_sentences_across_scenes_count():
    assert "ia-phrases-courtes" in codes_in(part_of("Il dort.", "Il rêve.", "Il oublie."), "fr")


def test_capitals_in_say_only_outside_known_acronyms():
    assert "ia-majuscules" in codes_in(part_of("Ce résultat est ÉNORME pour tout le monde ici."))
    for ok in ("L'OTAN et les BRICS", "Le PIB et l'ONU", "Louis XVIII et la NASA", "Les USA aussi", "Il a dit OK"):
        assert "ia-majuscules" not in codes_in(part_of(ok + " en parlent beaucoup ensemble."))
    assert "ia-majuscules" not in codes_in(part_of(NEUTRAL, props={0: {"text": "ÉNORME"}}))


def test_quotes_in_say_but_not_in_a_quote_scene():
    assert "ia-guillemets" in codes_in(part_of("Il a dit « bonjour » à tout le monde ici présent."))
    assert "ia-guillemets" in codes_in(part_of('Il a dit "bonjour" à tout le monde ici présent.'))
    assert "ia-guillemets" not in codes_in(part_of("Il a dit « bonjour » à tout le monde ici présent.", kinds={0: "quote"},
                                                  props={0: {"text": "bonjour"}}))
    assert "ia-guillemets" not in codes_in(part_of("L'homme d'à côté dit bonjour à tout le monde."))


def test_quote_text_and_speaker_are_never_scanned():
    quote = part_of("Voici ce que dit le chercheur.", kinds={0: "quote"},
                    props={0: {"text": "C'est incroyable – vraiment", "speaker": "Un expert \u2014 connu"}})
    assert codes_in(quote) == []


def test_one_finding_per_family_citing_the_first_occurrence():
    part = part_of("Une idée incroyable ici pour nous tous.", "Une autre idée fascinante ici pour nous tous.")
    found = [f for f in slop.findings(part, 1, "fr") if f[0] == "ia-mots-creux"]
    assert len(found) == 1 and found[0][1] == "Partie 1, scène 1" and "incroyable" in found[0][2]


def test_english_equivalents():
    cases = {"ia-mots-creux": "This is a groundbreaking idea for everyone here today.",
             "ia-annonce": "In this video we look at sleep and what it does to people.",
             "ia-fausse-confidence": "Honestly, nobody sleeps well in this city at night.",
             "ia-conclusion-vague": "Only time will tell what happens next to all of us."}
    for code, text in cases.items():
        assert code in codes_in(part_of(text, hook="Tell me why we forget ?"), "en"), code
    twice = part_of("It's not luck, it's a long habit for most people.", "Not only do we sleep badly, but we dream less.")
    assert "ia-formule-binaire" in codes_in(twice, "en")


def test_french_words_are_not_flagged_in_an_english_video_and_unknown_languages_get_the_neutral_checks():
    assert "ia-mots-creux" not in codes_in(part_of("Une idée incroyable ici."), "en")
    assert codes_in(part_of("Una idea incroyable aquí hoy."), "es") == []
    assert "ia-tiret" in codes_in(part_of("Una idea - aquí hoy para todos."), "es")


def test_findings_are_relire_lines_with_stable_codes_and_lessons(tmp_path):
    plan = {"version": 1, "lang": "fr", "parts": [part_of("Une idée incroyable ici pour nous tous.")]}
    pairs = review.coded(plan, tmp_path, 120)
    line = next(t for c, t in pairs if c == "ia-mots-creux")
    assert line.startswith("RELIRE : Partie 1, scène 1 : mot creux « incroyable »") and "fait précis" in line
    for code in ("ia-tiret", "ia-mots-creux", "ia-annonce", "ia-fausse-confidence", "ia-formule-binaire", "ia-phrases-courtes",
                 "ia-conclusion-vague", "ia-majuscules", "ia-guillemets"):
        assert code in codes.LESSONS and len(codes.LESSONS[code]) <= 200


def test_the_existing_em_dash_error_is_kept(job_with_fixtures):
    import json
    from ideo import plan_check

    plan = json.loads((job_with_fixtures / "plan.json").read_text(encoding="utf-8"))
    plan["parts"][0]["scenes"][0]["say"] += " Un tiret " + chr(0x2014) + " ici."
    (job_with_fixtures / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    assert any("tiret cadratin interdit" in e for e in plan_check.check_plan(job_with_fixtures))
