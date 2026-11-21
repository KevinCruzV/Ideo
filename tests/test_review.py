import copy

import pytest

from ideo import common, review


def scene(kind="stamp", say="Une phrase de huit mots exactement, ni plus ni moins.", props=None, **extra):
    return {"type": kind, "say": say, "props": props or {"text": "T"}, "src": "0:10", **extra}


def plan_of(*scenes, kicker=True):
    scenes = list(scenes)
    if kicker:
        scenes[0] = copy.deepcopy(scenes[0])
        scenes[0]["props"] = {**scenes[0]["props"], "kicker": "1991"}
    return {"version": 1, "lang": "fr", "parts": [{"n": 1, "title": "T", "hook": "H", "scenes": scenes}]}


@pytest.fixture
def job(tmp_path):
    common.save_json(tmp_path / "info.json", {"duration": 600})
    return tmp_path


def texts(plan, job, seconds=120):
    return review.findings(plan, job, seconds)


def only(plan, job, fragment, seconds=120):
    return [t for t in texts(plan, job, seconds) if fragment in t]


def varied(n):
    kinds = ["stamp", "key-title", "quote", "counter", "person-card", "mascot", "stamp"]
    return [scene(kinds[i % 2 * 0 + i % 7] if False else ("stamp" if i % 2 == 0 else "person-card"),
                  props={"text": "x"} if i % 2 == 0 else {"name": "x", "picto": "globe"}) for i in range(n)]


def test_every_line_has_the_relire_format(job):
    plan = plan_of(scene(say="court"))
    assert all(t.startswith("RELIRE : ") and t.count(" : ") >= 2 for t in texts(plan, job))


def test_year_in_say_without_date_on_screen(job):
    plan = plan_of(scene(say="En 1991 le bloc de l'Est s'est effondré et tout a changé pour les peuples."), kicker=False)
    assert only(plan, job, "année")
    assert not only(plan_of(scene(say="En 1991 le bloc de l'Est s'est effondré et tout a changé pour les peuples.")), job, "année")
    with_text = plan_of(scene(say="En 1991 le bloc de l'Est s'est effondré et tout a changé pour les peuples.",
                              props={"text": "1991"}), kicker=False)
    assert not only(with_text, job, "année")


def test_year_regex_bounds(job):
    for say, expected in [("En 999 c'est loin pour nous tous ici présents", False), ("En 2100 on verra bien ce qui arrive", True),
                          ("En 2101 on ne sait pas non plus ce qui arrive", False), ("Il en a 12345 en tout dans la boite", False)]:
        assert bool(only(plan_of(scene(say=say), kicker=False), job, "année")) is expected, say


def test_less_than_half_the_scenes_with_a_drawing(job):
    plan = plan_of(*[scene() for _ in range(4)], scene(kind="mascot", props={"bubble": "b"}))
    found = only(plan, job, "dessin")
    assert found and "scène" in found[0]
    drawn = plan_of(*[scene(props={"text": "T", "picto": "globe"}) for _ in range(3)], scene())
    assert not only(drawn, job, "dessin")


def test_longest_scenes_without_drawing_are_named(job):
    long_say = " ".join(["mot"] * 25)
    plan = plan_of(scene(), scene(say=long_say), scene(), scene(say=long_say + " de plus"))
    found = only(plan, job, "dessin")[0]
    assert "2" in found and "4" in found


def test_bare_name_lists(job):
    bare = plan_of(scene(kind="fact-chips", props={"chips": ["Chine", "Inde", "Brésil"]}))
    assert only(bare, job, "noms nus")
    figures = plan_of(scene(kind="fact-chips", props={"chips": ["Chine 18 %", "Inde", "Brésil"]}))
    assert not only(figures, job, "noms nus")
    long = plan_of(scene(kind="stack-list", props={"items": ["Les trois grands pays", "Un autre long libellé"]}))
    assert not only(long, job, "noms nus")
    grid = plan_of(scene(kind="icon-grid", props={"cells": [{"label": "Chine"}, {"label": "Inde"}]}))
    assert only(grid, job, "noms nus")


def test_bar_diagram_without_unit(job):
    bar = plan_of(scene(kind="shape-diagram", props={"values": [1, 2], "shape": "bar"}))
    assert only(bar, job, "unité")
    with_unit = plan_of(scene(kind="shape-diagram", props={"values": [1, 2], "shape": "bar", "unit": "%"}))
    assert not only(with_unit, job, "unité")
    circle = plan_of(scene(kind="shape-diagram", props={"values": [1, 2], "shape": "circle"}))
    assert not only(circle, job, "unité")


@pytest.mark.parametrize("word", ["morts", "victimes", "attentat", "décès"])
def test_counter_on_grave_subject(job, word):
    plan = plan_of(scene(kind="counter", say=f"On compte des milliers de {word} dans cette terrible guerre civile.",
                         props={"to": 5000}))
    assert only(plan, job, "sujet grave")


def test_counter_on_neutral_subject_is_fine(job):
    plan = plan_of(scene(kind="counter", say="La population atteint cinq millions d'habitants dans cette région.",
                         props={"to": 5}))
    assert not only(plan, job, "sujet grave")


def test_same_type_twice_in_a_row(job):
    assert only(plan_of(scene(), scene()), job, "du même type")
    assert not only(plan_of(scene(), scene(kind="person-card", props={"name": "n"})), job, "du même type")


def test_more_than_four_mascots(job):
    many = plan_of(*[scene(kind="mascot" if i % 2 else "stamp", props={"bubble": "b"} if i % 2 else {"text": "t"}) for i in range(12)])
    assert only(many, job, "mascot")
    few = plan_of(*[scene(kind="mascot" if i % 4 == 1 else "stamp", props={"bubble": "b"} if i % 4 == 1 else {"text": "t"}) for i in range(8)])
    assert not only(few, job, "« mascot »")


def test_key_title_frequency(job):
    plan = plan_of(*[scene(kind="key-title" if i < 3 else "stamp") for i in range(6)])
    assert only(plan, job, "key-title")
    ok = plan_of(scene(kind="key-title"), *[scene() for _ in range(5)])
    assert not only(ok, job, "« key-title » pour")


def test_scene_too_long_or_too_short(job):
    plan = plan_of(scene(say=" ".join(["mot"] * 31)), scene(say="Trop court"))
    assert only(plan, job, "plus de 30 mots") and only(plan, job, "moins de 8 mots")
    ok = plan_of(scene(say=" ".join(["mot"] * 30)), scene(say=" ".join(["mot"] * 8)))
    assert not only(ok, job, "plus de 30") and not only(ok, job, "moins de 8")


def test_last_scene_is_a_question(job):
    plan = plan_of(scene(), scene(say="Alors, qui va dominer le monde dans les prochaines décennies ?"))
    assert only(plan, job, "question")
    assert not only(plan_of(scene(say="Voilà la réponse à toutes les questions que nous nous posions ici.")), job, "question")


def test_no_kicker_in_the_plan(job):
    assert only(plan_of(scene(), kicker=False), job, "kicker")
    assert not only(plan_of(scene()), job, "aucun « kicker »")


def test_three_says_starting_with_the_same_word(job):
    same = [scene(say="Le monde change vite autour de nous aujourd'hui."), scene(say="Le bloc de l'Est s'est effondré net."),
            scene(say="Le dernier chef a démissionné ce soir là.")]
    assert only(plan_of(*same), job, "commencent par")
    assert not only(plan_of(*same[:2]), job, "commencent par")


def test_chopped_rhythm(job):
    plan = plan_of(*[scene() for _ in range(10)])
    assert only(plan, job, "par minute", seconds=60)
    assert not only(plan, job, "par minute", seconds=120)


def test_skimming_the_whole_source_in_little_time(job):
    plan = plan_of(scene(src="0:10"), scene(src="9:30"))
    assert only(plan, job, "survoles toute la source", seconds=60)
    assert not only(plan, job, "survoles toute la source", seconds=150)
    near = plan_of(scene(src="0:10"), scene(src="1:30"))
    assert not only(near, job, "survoles toute la source", seconds=60)


def test_findings_are_sorted_by_importance_and_capped(job):
    scenes = [scene(say="court") for _ in range(30)]
    plan = plan_of(*scenes, scene(say="Une question ?"), kicker=False)
    lines = review.relire(job, plan, 40)
    assert 1 < len(lines) <= review.LIMIT
    assert "par minute" in lines[0] or "question" in lines[0]
    assert "kicker" in lines[-1] or "même type" in lines[-1] or "moins de" in lines[-1] or "commencent" in lines[-1]


def test_findings_are_capped(job, monkeypatch):
    monkeypatch.setattr(review, "LIMIT", 2)
    plan = plan_of(*[scene(say="court") for _ in range(5)], kicker=False)
    assert len(review.relire(job, plan, 120)) == 2


def test_review_stops_after_two_passes_and_is_recorded(job):
    plan = plan_of(scene(say="court"), kicker=False)
    assert review.relire(job, plan, 120)
    assert review.passes(job) == 1
    assert review.relire(job, plan, 120)
    assert review.relire(job, plan, 120) == []
    assert review.passes(job) == 2


def test_clean_plan_has_no_findings_and_records_nothing(job):
    ok = plan_of(*[scene(props={"text": "T", "picto": "globe"}, kind="stamp" if i % 2 else "quote",
                         say="En 1991 le bloc de l'Est s'est effondré proprement." if i == 0 else
                         ["Alors le monde a changé de visage pour tous.", "Voici la suite de cette longue histoire commune."][i % 2])
                  for i in range(4)])
    assert review.relire(job, ok, 120) == []
    assert review.passes(job) == 0


def test_reset_clears_the_pass_counter(job):
    plan = plan_of(scene(say="court"), kicker=False)
    review.relire(job, plan, 120)
    review.relire(job, plan, 120)
    assert review.relire(job, plan, 120) == []
    review.reset(job)
    assert review.passes(job) == 0 and review.relire(job, plan, 120)


def test_codes_are_stable_and_messages_unchanged(job):
    plan = plan_of(scene(kind="shape-diagram", props={"values": [1, 2], "shape": "bar"}, say="court"), kicker=False)
    pairs = review.coded(plan, job, 120)
    codes = [c for c, _ in pairs]
    assert "barres-sans-unite" in codes and "say-trop-court" in codes and "sans-kicker" in codes
    assert all(t.startswith("RELIRE : ") for _, t in pairs)
    assert [t for _, t in pairs] == review.findings(plan, job, 120)
    assert all(c == c.lower() and " " not in c for c in codes)


def test_three_word_names_are_bare_too(job):
    grid = plan_of(scene(kind="icon-grid", props={"cells": [{"label": l, "shape": "circle"} for l in
                                                           ["Russie", "Inde", "Chine", "Afrique du Sud"]]}))
    assert only(grid, job, "noms nus")
    assert only(plan_of(scene(kind="stack-list", props={"items": ["Afrique du Sud", "Corée du Nord"]})), job, "noms nus")
    assert not only(plan_of(scene(kind="stack-list", props={"items": ["Les États Unis d'Amérique", "Un long nom"]})), job, "noms nus")


def test_icon_grid_without_any_picto_is_flagged_even_with_long_labels(job):
    long_labels = plan_of(scene(kind="icon-grid", props={"cells": [{"label": "Les grandes puissances du monde"},
                                                                    {"label": "Les petits pays en développement"}]}))
    assert only(long_labels, job, "noms nus") or only(long_labels, job, "sans dessin")
    drawn = plan_of(scene(kind="icon-grid", props={"cells": [{"label": "Les grandes puissances du monde", "picto": "globe"},
                                                              {"label": "Les petits pays en développement"}]}))
    assert not only(drawn, job, "noms nus")


def test_more_than_three_versus_scenes(job):
    many = plan_of(*[scene(kind="versus" if i % 2 else "stamp", props={"left": "a", "right": "b"} if i % 2 else {"text": "t"})
                     for i in range(10)])
    found = [c for c, _ in review.coded(many, job, 120) if c == "trop-de-versus"]
    assert found
    few = plan_of(*[scene(kind="versus" if i % 3 == 1 else "stamp", props={"left": "a", "right": "b"} if i % 3 == 1 else {"text": "t"})
                    for i in range(9)])
    assert "trop-de-versus" not in [c for c, _ in review.coded(few, job, 120)]


def test_counter_without_unit_when_say_talks_percent(job):
    for say in ["La part atteint vingt pour cent de la richesse mondiale totale.", "La part atteint 20 % de la richesse mondiale totale."]:
        assert only(plan_of(scene(kind="counter", say=say, props={"to": 20})), job, "compteur sans unité"), say
    assert not only(plan_of(scene(kind="counter", say="La part atteint 20 % de la richesse mondiale totale.",
                                  props={"to": 20, "unit": "%"})), job, "compteur sans unité")
    assert not only(plan_of(scene(kind="counter", say="La population atteint cinq millions d'habitants.", props={"to": 5})),
                    job, "compteur sans unité")


LONG_SAY_TEXT = "Le premier pays signe un accord puis le second pays refuse de signer et ensuite les marchés réagissent très fort partout dans le monde entier"


def test_items_grouped_in_the_first_half(job):
    early = scene(say=LONG_SAY_TEXT, props={"text": "T"}, items=[{"el": "text", "on": "premier"}, {"el": "text", "on": "accord"}])
    assert only(plan_of(early), job, "groupés au début")
    spread = scene(say=LONG_SAY_TEXT, props={"text": "T"}, items=[{"el": "text", "on": "premier"}, {"el": "text", "on": "monde"}])
    assert not only(plan_of(spread), job, "groupés au début")
    short = scene(say="Un accord est signé.", items=[{"el": "text", "on": "accord"}])
    assert not only(plan_of(short), job, "groupés au début")
    assert not only(plan_of(scene(say=LONG_SAY_TEXT)), job, "groupés au début")


def test_grouped_items_advice_names_the_last_sentence(job):
    early = scene(say=LONG_SAY_TEXT, items=[{"el": "text", "on": "premier"}])
    line = only(plan_of(early), job, "groupés au début")[0]
    assert "dernière phrase" in line


def test_long_video_without_any_act_pause(job):
    plan = plan_of(*[scene() for _ in range(11)])
    found = [c for c, _ in review.coded(plan, job, 200) if c == "sans-pause-d-acte"]
    assert found
    line = only(plan, job, "pause d'acte", seconds=200)[0]
    assert '"break": true' in line
    marked = plan_of(*[scene() for _ in range(11)])
    marked["parts"][0]["scenes"][5]["break"] = True
    assert "sans-pause-d-acte" not in [c for c, _ in review.coded(marked, job, 200)]
    assert "sans-pause-d-acte" not in [c for c, _ in review.coded(plan_of(*[scene() for _ in range(10)]), job, 200)]


def codes_of(plan, job, seconds=120):
    return [c for c, _ in review.coded(plan, job, seconds)]


def test_country_name_without_its_flag(job):
    grid = plan_of(scene(kind="icon-grid", props={"cells": [{"label": "Chine", "picto": "globe"}, {"label": "Inde", "shape": "circle"}]}))
    found = [t for c, t in review.coded(grid, job, 120) if c == "pays-sans-drapeau"]
    assert len(found) == 1 and "Partie 1, scène 1" in found[0]
    assert "flag:cn" in found[0] and "flag:in" in found[0] and found[0].startswith("RELIRE : ")


def test_country_with_its_flag_is_fine(job):
    grid = plan_of(scene(kind="icon-grid", props={"cells": [{"label": "Chine", "picto": "flag:cn"}, {"label": "Inde", "picto": "flag:in"}]}))
    assert "pays-sans-drapeau" not in codes_of(grid, job)
    one = plan_of(scene(kind="icon-grid", props={"cells": [{"label": "Chine", "picto": "flag:cn"}, {"label": "Inde", "picto": "globe"}]}))
    found = [t for c, t in review.coded(one, job, 120) if c == "pays-sans-drapeau"]
    assert len(found) == 1 and "flag:in" in found[0] and "flag:cn" not in found[0]


def test_versus_sides_chips_and_stack_items(job):
    versus = plan_of(scene(kind="versus", props={"left": "États-Unis", "right": "URSS"}))
    text = [t for c, t in review.coded(versus, job, 120) if c == "pays-sans-drapeau"][0]
    assert "flag:us" in text and "flag:su" in text and "left_picto" in text
    assert "pays-sans-drapeau" not in codes_of(plan_of(scene(kind="versus", props={
        "left": "États-Unis", "right": "URSS", "left_picto": "flag:us", "right_picto": "flag:su"})), job)
    assert "pays-sans-drapeau" in codes_of(plan_of(scene(kind="fact-chips", props={"chips": ["Chine", "x 12"]})), job)
    assert "pays-sans-drapeau" in codes_of(plan_of(scene(kind="stack-list", props={"items": ["Brazil", "Inde 2e"]})), job)


def test_scene_picto_flag_counts_for_lists(job):
    ok = plan_of(scene(kind="stack-list", props={"items": ["Chine", "autre chose"], "picto": "flag:cn"}))
    assert "pays-sans-drapeau" not in codes_of(ok, job)


def test_not_a_bare_country_name_is_not_flagged(job):
    plan = plan_of(scene(kind="fact-chips", props={"chips": ["Chine 18 %", "La Chine", "Paris"]}))
    assert "pays-sans-drapeau" not in codes_of(plan, job)
    assert "pays-sans-drapeau" not in codes_of(plan_of(scene(kind="stamp", props={"text": "Chine"})), job)


def test_overloaded_scenes(job):
    long = "Un texte assez long pour dépasser"
    marks = [{"at": "1991", "label": "Une très longue étiquette de repère ici"}] * 5
    assert "scene-trop-chargee" in codes_of(plan_of(scene(kind="timeline", props={"marks": marks})), job)
    assert "scene-trop-chargee" not in codes_of(plan_of(scene(kind="timeline", props={"marks": marks[:4]})), job)
    short = [{"at": "1991", "label": "Court"}] * 5
    assert "scene-trop-chargee" not in codes_of(plan_of(scene(kind="timeline", props={"marks": short})), job)
    items = ["Un élément de liste vraiment très long pour tester la charge"] * 5
    assert "scene-trop-chargee" in codes_of(plan_of(scene(kind="stack-list", props={"items": items})), job)
    assert "scene-trop-chargee" not in codes_of(plan_of(scene(kind="stack-list", props={"items": items[:4]})), job)
    cells = [{"label": "Un libellé long"}] * 7
    assert "scene-trop-chargee" in codes_of(plan_of(scene(kind="icon-grid", props={"cells": cells})), job)
    assert "scene-trop-chargee" not in codes_of(plan_of(scene(kind="icon-grid", props={"cells": cells[:6]})), job)
    assert "scene-trop-chargee" not in codes_of(plan_of(scene(kind="icon-grid", props={"cells": [{"label": "Court"}] * 8})), job)
    values = {"values": [1, 2, 3, 4, 5, 6], "labels": ["Un libellé long"] * 6}
    assert "scene-trop-chargee" in codes_of(plan_of(scene(kind="shape-diagram", props=values)), job)
    assert "scene-trop-chargee" not in codes_of(plan_of(scene(kind="shape-diagram", props={**values, "values": [1, 2, 3, 4, 5], "labels": values["labels"][:5]})), job)
    assert long


def test_overloaded_advice_says_to_split(job):
    items = ["Un élément de liste vraiment très long pour tester la charge"] * 5
    line = [t for c, t in review.coded(plan_of(scene(kind="stack-list", props={"items": items})), job, 120)
            if c == "scene-trop-chargee"][0]
    assert line.startswith("RELIRE : Partie 1, scène 1 :") and "deux scènes" in line and "téléphone" in line


def test_new_lessons_exist():
    from ideo import codes

    assert "flag:" in codes.LESSONS["pays-sans-drapeau"] and "scene-trop-chargee" in codes.LESSONS
    assert codes.error_code("S : « props.picto » : « flag:xx » n'est pas un drapeau connu. Écris") == "drapeau-inconnu"
