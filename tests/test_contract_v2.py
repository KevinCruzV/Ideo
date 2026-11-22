import json

import pytest

from ideo import plan_check, scene_schema

PICTOS_TEXT = ("globe, flag, pin, city, house, factory, bank, coin, chart-up, chart-down, ship, plane, train, rocket, "
               "satellite, tank, shield, sword, bomb, dove, handshake, justice, wall, chain, lock, key, crown, ballot, "
               "megaphone, newspaper, tv, phone, computer, chip, book, brain, heart, eye, clock, calendar, lightbulb, "
               "atom, flask, leaf, sun, drop, fire, lightning, mountain, barrel, gear, people")


HEALTH_PICTOS = ("lungs, stomach, spine, bone, muscle, tooth, blood, pill, syringe, virus, bed, pillow, moon, thermometer, "
                 "scale-weight, apple, dumbbell, running-shoe, stethoscope, hospital")


def test_pictos_are_the_52_names_of_the_contract_plus_the_20_health_ones():
    assert scene_schema.PICTOS == tuple(PICTOS_TEXT.split(", ")) + tuple(HEALTH_PICTOS.split(", "))
    assert len(scene_schema.PICTOS) == 72 == len(set(scene_schema.PICTOS))


KICKER_KINDS = {
    "key-title": {"text": "T"}, "person-card": {"name": "N"}, "fact-chips": {"chips": ["a"]},
    "stack-list": {"items": ["a"]}, "counter": {"to": 3}, "timeline": {"marks": [{"at": "1900"}]},
    "icon-grid": {"cells": [{"label": "a"}]}, "stamp": {"text": "T"}, "quote": {"text": "T"},
    "object-state": {"object": "jar", "states": ["a"]}, "shape-diagram": {"values": [1]},
    "mascot": {"bubble": "B"}, "versus": {"left": "A", "right": "B"},
}


@pytest.mark.parametrize("kind", sorted(KICKER_KINDS))
def test_kicker_is_accepted_on_every_type_with_a_cap_of_28(kind):
    props = {**KICKER_KINDS[kind], "kicker": "Mars 1991"}
    assert scene_schema.check_props(kind, props, "x") == []
    props["kicker"] = "x" * 29
    errors = scene_schema.check_props(kind, props, "x")
    assert len(errors) == 1 and "kicker" in errors[0] and "28" in errors[0]


@pytest.mark.parametrize("kind", ["key-title", "person-card", "fact-chips", "stack-list", "counter", "timeline", "stamp", "quote"])
def test_picto_accepted_on_its_types_and_checked(kind):
    assert scene_schema.check_props(kind, {**KICKER_KINDS[kind], "picto": "globe"}, "x") == []
    errors = scene_schema.check_props(kind, {**KICKER_KINDS[kind], "picto": "licorne"}, "x")
    assert len(errors) == 1 and "picto" in errors[0] and "globe" in errors[0]


@pytest.mark.parametrize("kind", ["icon-grid", "object-state", "shape-diagram", "mascot", "versus"])
def test_picto_is_refused_on_other_types(kind):
    errors = scene_schema.check_props(kind, {**KICKER_KINDS[kind], "picto": "globe"}, "x")
    assert errors and "prop inconnue" in errors[0]


def test_icon_grid_cell_picto():
    ok = {"cells": [{"label": "a", "picto": "bank"}, {"label": "b", "shape": "circle"}]}
    assert scene_schema.check_props("icon-grid", ok, "x") == []
    bad = {"cells": [{"label": "a", "picto": "licorne"}]}
    assert scene_schema.check_props("icon-grid", bad, "x")


def test_shape_diagram_unit_cap_8():
    assert scene_schema.check_props("shape-diagram", {"values": [1], "unit": "Md$"}, "x") == []
    errors = scene_schema.check_props("shape-diagram", {"values": [1], "unit": "milliards"}, "x")
    assert len(errors) == 1 and "unit" in errors[0] and "8" in errors[0]


def test_versus_props_caps_and_el():
    props = {"left": "Nord", "right": "Sud", "left_picto": "flag", "right_picto": "ship"}
    assert scene_schema.check_props("versus", props, "x") == []
    assert scene_schema.check_props("versus", {"left": "Nord"}, "x")
    assert scene_schema.check_props("versus", {"left": "x" * 25, "right": "Sud"}, "x")
    assert scene_schema.check_el("versus", props, "left", "x") == []
    assert scene_schema.check_el("versus", props, "right", "x") == []
    assert scene_schema.check_el("versus", props, "middle", "x")


def test_versus_is_a_scene_type():
    assert "versus" in plan_check.SCENE_TYPES
    assert set(scene_schema.SCHEMA) == set(plan_check.SCENE_TYPES)


def plan_with(job, mutate):
    path = job / "plan.json"
    plan = json.loads(path.read_text(encoding="utf-8"))
    mutate(plan)
    path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    return plan_check.check_plan(job)


def test_numeric_on_is_accepted(job_with_fixtures):
    def mutate(plan):
        scene = plan["parts"][0]["scenes"][2]
        scene["say"] = scene["say"] + " en 1885"
        scene["items"] = [{"el": "chips.0", "on": 1885}]

    assert plan_with(job_with_fixtures, mutate) == []


def test_boolean_on_is_refused(job_with_fixtures):
    def mutate(plan):
        plan["parts"][0]["scenes"][2]["items"] = [{"el": "chips.0", "on": True}]

    assert plan_with(job_with_fixtures, mutate)


def test_scene_cap_is_45_per_part(job_with_fixtures):
    def mutate(plan):
        scenes = plan["parts"][0]["scenes"]
        plan["parts"][0]["scenes"] = [scenes[0]] * 46

    errors = plan_with(job_with_fixtures, mutate)
    assert any("46 scènes" in e and "45" in e and e.startswith("Partie 1") for e in errors)


def test_45_scenes_are_not_refused_for_the_count(job_with_fixtures):
    def mutate(plan):
        plan["parts"][0]["scenes"] = [plan["parts"][0]["scenes"][0]] * 45

    assert not any("scènes," in e and "au plus" in e for e in plan_with(job_with_fixtures, mutate))


def test_counter_unit_cap_4():
    assert scene_schema.check_props("counter", {"to": 20, "unit": "%"}, "x") == []
    errors = scene_schema.check_props("counter", {"to": 20, "unit": "milli"}, "x")
    assert len(errors) == 1 and "unit" in errors[0] and "4" in errors[0]
    assert scene_schema.check_props("counter", {"to": 20, "unit": ""}, "x")


def test_wishes_absent_is_normal(job_with_fixtures):
    assert plan_check.check_plan(job_with_fixtures) == []


def test_valid_wishes(job_with_fixtures):
    assert plan_with(job_with_fixtures, lambda p: p.update(wishes=["drapeau américain", "carte du monde"])) == []
    assert plan_with(job_with_fixtures, lambda p: p.update(wishes=[])) == []
    assert plan_with(job_with_fixtures, lambda p: p.update(wishes=["x" * 40] * 5)) == []


def test_wishes_must_be_a_list_of_at_most_five(job_with_fixtures):
    for bad in ("drapeau", ["a"] * 6, {"a": 1}):
        errors = plan_with(job_with_fixtures, lambda p, b=bad: p.update(wishes=b))
        assert len(errors) == 1 and errors[0].startswith("Plan : « wishes » doit être une liste de 0 à 5 textes")


def test_wish_must_be_a_short_non_empty_text(job_with_fixtures):
    errors = plan_with(job_with_fixtures, lambda p: p.update(wishes=["", 3, "x" * 41]))
    assert len(errors) == 3
    assert errors[0].startswith("Plan : « wishes.0 » doit être un texte non vide")
    assert errors[1].startswith("Plan : « wishes.1 » doit être un texte non vide")
    assert errors[2].startswith("Plan : « wishes.2 » fait 41 caractères, 40 au plus")


def test_wish_with_em_dash_is_refused(job_with_fixtures):
    errors = plan_with(job_with_fixtures, lambda p: p.update(wishes=["a " + chr(0x2014) + " b"]))
    assert errors and "tiret cadratin" in errors[0]


def test_break_must_be_a_boolean(job_with_fixtures):
    assert plan_with(job_with_fixtures, lambda p: p["parts"][0]["scenes"][1].update({"break": True})) == []
    assert plan_with(job_with_fixtures, lambda p: p["parts"][0]["scenes"][1].update({"break": False})) == []
    errors = plan_with(job_with_fixtures, lambda p: p["parts"][0]["scenes"][1].update({"break": "oui"}))
    assert errors == ["Partie 1, scène 2 : « break » doit être true ou false (nouvel acte, pause avant la scène). Retire-le ou corrige-le."]
    from ideo import codes

    assert codes.error_code(errors[0]) == "break-invalide"


def test_flags_are_accepted_wherever_a_picto_is():
    assert scene_schema.check_props("key-title", {"text": "T", "picto": "flag:cn"}, "x") == []
    assert scene_schema.check_props("person-card", {"name": "N", "picto": "flag:fr"}, "x") == []
    assert scene_schema.check_props("versus", {"left": "a", "right": "b", "left_picto": "flag:us", "right_picto": "flag:su"}, "x") == []
    assert scene_schema.check_props("icon-grid", {"cells": [{"label": "a", "picto": "flag:in"}, {"label": "b", "picto": "globe"}]}, "x") == []


def test_special_flag_codes():
    for code in ("eu", "un", "su"):
        assert code in scene_schema.FLAGS


def test_flags_list_has_no_hateful_regime_and_is_sorted_two_letter_codes():
    assert len(scene_schema.FLAGS) == len(set(scene_schema.FLAGS)) == 252
    assert all(len(c) == 2 and c == c.lower() for c in scene_schema.FLAGS)
    assert "xx" not in scene_schema.FLAGS


@pytest.mark.parametrize("value", ["flag:xx", "flag:", "flag:FR", "flag:fra", "flag:fr "])
def test_unknown_flag_codes_say_what_to_write(value):
    errors = scene_schema.check_props("key-title", {"text": "T", "picto": value}, "Partie 1, scène 2")
    assert len(errors) == 1
    assert errors[0].startswith("Partie 1, scène 2 : « props.picto » : « " + value + " » n'est pas un drapeau connu.")
    assert "deux lettres en minuscules" in errors[0]
    assert all(f"flag:{c}" in errors[0] for c in ("fr", "us", "cn", "de", "br", "za"))


def test_unknown_flag_in_a_grid_cell_gives_one_precise_error():
    errors = scene_schema.check_props("icon-grid", {"cells": [{"label": "a", "picto": "flag:zz"}]}, "x")
    assert len(errors) == 1 and "props.cells.0.picto" in errors[0]


def test_unknown_flag_does_not_hide_other_problems_in_the_same_list():
    errors = scene_schema.check_props("icon-grid", {"cells": [{"label": "a", "picto": "flag:zz", "icon": 1}]}, "x")
    assert len(errors) == 2


def test_plain_unknown_picto_still_lists_the_names_and_the_flag_form():
    errors = scene_schema.check_props("key-title", {"text": "T", "picto": "licorne"}, "x")
    assert len(errors) == 1 and "globe" in errors[0] and "flag:<code>" in errors[0]


PERSON = {"name": "N", "hair": "crown-bald", "hair_color": "grey", "facial": "goatee", "hat": "wig", "glasses": True,
          "outfit": "lab-coat", "skin": "dark"}


def test_person_card_accepts_every_character_prop():
    assert scene_schema.check_props("person-card", PERSON, "x") == []
    assert scene_schema.check_props("person-card", {"name": "N"}, "x") == []
    assert scene_schema.check_props("person-card", {**PERSON, "glasses": False}, "x") == []


@pytest.mark.parametrize("prop,bad", [("hair", "chauve"), ("hair_color", "bleu"), ("facial", "tresse"), ("hat", "casque"),
                                      ("outfit", "pyjama"), ("skin", "vert"), ("glasses", "oui"), ("glasses", 1)])
def test_person_card_closed_values_are_checked(prop, bad):
    errors = scene_schema.check_props("person-card", {"name": "N", prop: bad}, "x")
    assert len(errors) == 1 and f"« props.{prop} » doit être" in errors[0]
    assert ("true ou false" in errors[0]) if prop == "glasses" else ("une de ces valeurs :" in errors[0])


def test_person_card_value_lists_are_the_contract_ones():
    assert scene_schema.HAIRS == ("none", "short", "side", "long", "curly", "wild", "bun", "crown-bald")
    assert scene_schema.HATS[-1] == "wig" and len(scene_schema.HATS) == 11
    assert scene_schema.OUTFITS == ("suit", "uniform", "robe", "lab-coat", "casual", "toga", "armor", "dress")


def ts_names(path, name):
    import re
    from pathlib import Path

    file = Path(__file__).resolve().parent.parent / "render" / "src" / path
    if not file.exists():
        pytest.skip(f"{path} n'existe pas encore dans le rendu")
    source = file.read_text(encoding="utf-8")
    block = re.search(rf"export const {name} = \[(.*?)\]", source, re.S).group(1)
    return tuple(re.findall(r'"([\w-]+)"', block))


def test_map_codes_and_zones_are_the_ones_of_the_render():
    assert ts_names("map/codes.ts", "MAP_CODES") == scene_schema.MAP_CODES
    assert ts_names("map/codes.ts", "MAP_FOCUS") == scene_schema.MAP_FOCUS
    assert len(scene_schema.MAP_CODES) == 235


def test_map_codes_are_flags_without_the_special_ones():
    assert set(scene_schema.MAP_CODES) <= set(scene_schema.FLAGS)
    assert not {"eu", "un", "su"} & set(scene_schema.MAP_CODES)
    assert len(set(scene_schema.FLAGS) - set(scene_schema.MAP_CODES)) == 17


@pytest.mark.parametrize("name,attr", [("BODY_POSES", "BODY_POSES"), ("BODY_SETTINGS", "BODY_SETTINGS"),
                                       ("BODY_PARTS", "BODY_PARTS"), ("BODY_TONES", "BODY_TONES")])
def test_body_values_are_the_ones_of_the_render(name, attr):
    assert ts_names("scenes/bodyOptions.ts", name) == getattr(scene_schema, attr)


MAP = {"focus": "asia", "places": [{"code": "cn", "label": "Chine"}, {"code": "in"}], "route": ["cn", "in"]}


def test_map_scene_accepts_the_contract():
    assert scene_schema.check_props("map", MAP, "x") == []
    assert scene_schema.check_props("map", {"focus": "world", "places": [{"code": "us"}]}, "x") == []
    assert scene_schema.check_props("map", {**MAP, "kicker": "1949"}, "x") == []
    assert scene_schema.check_props("map", {"focus": "oceania", "places": [{"code": "au"}] * 6}, "x") == []


@pytest.mark.parametrize("props,fragment", [
    ({"places": [{"code": "cn"}]}, "prop « focus » manquante"),
    ({"focus": "asia"}, "prop « places » manquante"),
    ({"focus": "mars", "places": [{"code": "cn"}]}, "« props.focus » doit être une de ces valeurs"),
    ({"focus": "asia", "places": []}, "liste de 1 à 6 objets"),
    ({"focus": "asia", "places": [{"code": "cn"}] * 7}, "liste de 1 à 6 objets"),
    ({"focus": "asia", "places": [{"label": "x"}]}, "« props.places »"),
    ({"focus": "asia", "places": [{"code": "CN"}]}, "n'a pas de contour sur la carte"),
    ({"focus": "asia", "places": [{"code": "cn"}], "route": ["cn"]}, "liste de 2 à 6 codes de pays"),
    ({"focus": "asia", "places": [{"code": "cn"}], "route": ["cn"] * 7}, "liste de 2 à 6 codes de pays"),
    ({"focus": "asia", "places": [{"code": "cn"}], "route": "cn"}, "liste de 2 à 6 codes de pays"),
    ({"focus": "asia", "places": [{"code": "cn"}], "extra": 1}, "prop inconnue « extra »"),
])
def test_map_scene_errors(props, fragment):
    errors = scene_schema.check_props("map", props, "Partie 1, scène 2")
    assert any(e.startswith("Partie 1, scène 2 : ") and fragment in e for e in errors), errors


def test_map_code_without_outline_says_it_simply():
    errors = scene_schema.check_props("map", {"focus": "africa", "places": [{"code": "re"}], "route": ["fr", "yt"]}, "x")
    assert len(errors) == 2
    assert "« props.places.0.code » : « re » n'a pas de contour sur la carte" in errors[0]
    assert "« props.route.1 » : « yt »" in errors[1]
    assert "par exemple cn, ru, in" in errors[0] and "eu, un, su" in errors[0] and "choisis un autre pays" in errors[0]


def test_map_code_problem_does_not_hide_other_problems():
    errors = scene_schema.check_props("map", {"focus": "mars", "places": [{"code": "re"}]}, "x")
    assert len(errors) == 2


def test_map_label_cap_24():
    errors = scene_schema.check_props("map", {"focus": "asia", "places": [{"code": "cn", "label": "x" * 25}]}, "x")
    assert len(errors) == 1 and "props.places.0.label" in errors[0] and "24" in errors[0]


def test_map_el():
    assert scene_schema.check_el("map", MAP, "places.1", "x") == []
    assert scene_schema.check_el("map", MAP, "route", "x") == []
    assert scene_schema.check_el("map", MAP, "places.2", "x")
    assert scene_schema.check_el("map", MAP, "places.<i>", "x")


BODY = {"pose": "lying-side-left", "setting": "bed", "tone": "good",
        "marks": [{"part": "back", "label": "Le dos"}, {"part": "hips"}]}


def test_body_scene_accepts_the_contract():
    assert scene_schema.check_props("body", BODY, "x") == []
    assert scene_schema.check_props("body", {"pose": "standing"}, "x") == []
    assert scene_schema.check_props("body", {"pose": "running", "marks": []}, "x") == []
    assert scene_schema.check_props("body", {**BODY, "kicker": "La nuit"}, "x") == []
    assert scene_schema.check_props("body", {"pose": "sitting", "marks": [{"part": "feet"}] * 4}, "x") == []


@pytest.mark.parametrize("props,fragment", [
    ({}, "prop « pose » manquante"),
    ({"pose": "dancing"}, "« props.pose » doit être une de ces valeurs : standing"),
    ({"pose": "standing", "setting": "pool"}, "« props.setting » doit être une de ces valeurs"),
    ({"pose": "standing", "tone": "red"}, "« props.tone » doit être une de ces valeurs : good, bad, neutral"),
    ({"pose": "standing", "marks": [{"part": "back"}] * 5}, "liste de 0 à 4 objets"),
    ({"pose": "standing", "marks": [{"part": "tail"}]}, "liste de 0 à 4 objets avec « part », « label »"),
    ({"pose": "standing", "marks": [{"label": "x"}]}, "« props.marks »"),
    ({"pose": "standing", "marks": "back"}, "« props.marks »"),
])
def test_body_scene_errors(props, fragment):
    errors = scene_schema.check_props("body", props, "Partie 1, scène 2")
    assert any(e.startswith("Partie 1, scène 2 : ") and fragment in e for e in errors), errors


def test_body_label_cap_28_and_el():
    errors = scene_schema.check_props("body", {"pose": "standing", "marks": [{"part": "back", "label": "x" * 29}]}, "x")
    assert len(errors) == 1 and "props.marks.0.label" in errors[0] and "28" in errors[0]
    assert scene_schema.check_el("body", BODY, "marks.1", "x") == []
    assert scene_schema.check_el("body", BODY, "marks.2", "x")


def test_new_scene_types_are_known_to_check(job_with_fixtures):
    assert {"map", "body"} <= plan_check.SCENE_TYPES
    assert set(scene_schema.SCHEMA) == set(plan_check.SCENE_TYPES)


def test_health_pictos_are_accepted():
    for name in HEALTH_PICTOS.split(", "):
        assert scene_schema.check_props("key-title", {"text": "T", "picto": name}, "x") == []
