import json

import pytest

from ideo import plan_check, scene_schema

PICTOS_TEXT = ("globe, flag, pin, city, house, factory, bank, coin, chart-up, chart-down, ship, plane, train, rocket, "
               "satellite, tank, shield, sword, bomb, dove, handshake, justice, wall, chain, lock, key, crown, ballot, "
               "megaphone, newspaper, tv, phone, computer, chip, book, brain, heart, eye, clock, calendar, lightbulb, "
               "atom, flask, leaf, sun, drop, fire, lightning, mountain, barrel, gear, people")


def test_pictos_are_the_52_names_of_the_contract():
    assert scene_schema.PICTOS == tuple(PICTOS_TEXT.split(", "))
    assert len(scene_schema.PICTOS) == 52


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


@pytest.mark.parametrize("kind", ["key-title", "fact-chips", "stack-list", "counter", "timeline", "stamp", "quote"])
def test_picto_accepted_on_its_types_and_checked(kind):
    assert scene_schema.check_props(kind, {**KICKER_KINDS[kind], "picto": "globe"}, "x") == []
    errors = scene_schema.check_props(kind, {**KICKER_KINDS[kind], "picto": "licorne"}, "x")
    assert len(errors) == 1 and "picto" in errors[0] and "globe" in errors[0]


@pytest.mark.parametrize("kind", ["person-card", "icon-grid", "object-state", "shape-diagram", "mascot", "versus"])
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
