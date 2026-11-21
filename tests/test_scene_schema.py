import json
import re
from pathlib import Path

import pytest

from ideo import plan_check, scene_schema

REPO = Path(__file__).resolve().parent.parent
ALL_SCENES = REPO / "render" / "fixtures" / "all-scenes.json"
SCENES_DIR = REPO / "render" / "src" / "scenes"
GUIDE = REPO / "skills" / "ideo" / "references" / "plan-guide.md"
COMPONENTS = {
    "key-title": "KeyTitle", "person-card": "PersonCard", "fact-chips": "FactChips", "stack-list": "StackList",
    "counter": "Counter", "timeline": "Timeline", "icon-grid": "IconGrid", "stamp": "Stamp", "quote": "Quote",
    "object-state": "ObjectState", "shape-diagram": "ShapeDiagram", "mascot": "Mascot",
}


def test_schema_covers_exactly_the_plan_types():
    assert set(scene_schema.SCHEMA) == set(plan_check.SCENE_TYPES)


def test_render_fixture_scenes_validate_against_schema():
    timeline = json.loads(ALL_SCENES.read_text(encoding="utf-8"))
    scenes = [s for s in timeline["segments"] if s["kind"] == "scene"]
    assert {s["type"] for s in scenes} == set(scene_schema.SCHEMA)
    for s in scenes:
        assert scene_schema.check_props(s["type"], s["props"], s["type"]) == []
        for item in s["items"]:
            assert scene_schema.check_el(s["type"], s["props"], item["el"], s["type"]) == []


def test_mascot_pose_fixture_validates_against_schema():
    timeline = json.loads((REPO / "render" / "fixtures" / "mascot-poses.json").read_text(encoding="utf-8"))
    scenes = [s for s in timeline["segments"] if s["kind"] == "scene"]
    assert {s["props"]["pose"] for s in scenes} == {"question", "surprise", "montre", "content"}
    for s in scenes:
        assert scene_schema.check_props(s["type"], s["props"], s["type"]) == []


@pytest.mark.parametrize("kind", sorted(COMPONENTS))
def test_schema_props_are_the_ones_the_component_reads(kind):
    source = (SCENES_DIR / f"{COMPONENTS[kind]}.tsx").read_text(encoding="utf-8")
    read = set(re.findall(r"props\.(\w+)", source))
    schema = scene_schema.SCHEMA[kind]
    assert read == set(schema["required"]) | set(schema["optional"])


@pytest.mark.parametrize("kind", sorted(COMPONENTS))
def test_guide_table_lists_schema_props(kind):
    row = next(line for line in GUIDE.read_text(encoding="utf-8").splitlines() if line.startswith(f"| `{kind}` |"))
    props_cell = row.split("|")[3]
    for prop in list(scene_schema.SCHEMA[kind]["required"]) + list(scene_schema.SCHEMA[kind]["optional"]):
        assert f"`{prop}`" in props_cell


@pytest.mark.parametrize("kind,props,fragment", [
    ("key-title", {"title": "x"}, "prop inconnue « title » pour « key-title ». Props acceptées : text, accent."),
    ("key-title", {"accent": "x"}, "prop « text » manquante pour « key-title »"),
    ("counter", {"to": "2300 mots"}, "« props.to » doit être un nombre"),
    ("fact-chips", {"chips": ["a"] * 7}, "« props.chips » doit être une liste de 1 à 6 textes"),
    ("fact-chips", {"chips": []}, "liste de 1 à 6 textes"),
    ("object-state", {"object": "fridge", "states": ["a"]}, "une de ces valeurs : screen, board, jar, door, scale"),
    ("icon-grid", {"cells": [{"shape": "star", "label": "a"}]}, "objets avec « shape », « label »"),
    ("icon-grid", {"cells": [{"label": "a", "icon": "x"}]}, "objets avec"),
    ("timeline", {"marks": [{"label": "a"}]}, "« props.marks »"),
    ("shape-diagram", {"values": ["1"]}, "liste de 1 à 8 nombres"),
    ("mascot", {"bubble": "Et alors ?", "pose": "colère"},
     "« props.pose » doit être une de ces valeurs : question, surprise, montre, content"),
    ("shape-diagram", {"values": [1, 2, 3], "labels": ["a", "b"]},
     "« props.labels » a 2 textes et « props.values » 3 nombres : donne autant de « labels » que de « values », sinon les étiquettes ne s'affichent pas."),
    ("key-title", {"text": "La courbe de l'oubli", "accent": "oubli"},
     "« props.accent » « oubli » n'est pas un mot de « props.text ». Recopie un mot ou une suite de mots exacts de « text »."),
    ("key-title", {"text": "Le ciel bleu", "accent": "rouge"}, "n'est pas un mot de « props.text »"),
])
def test_check_props_errors(kind, props, fragment):
    errors = scene_schema.check_props(kind, props, "Partie 1, scène 2")
    assert any(e.startswith("Partie 1, scène 2 : ") and fragment in e for e in errors), errors


@pytest.mark.parametrize("kind,props", [
    ("shape-diagram", {"values": [1, 2], "labels": ["a", "b"]}),
    ("shape-diagram", {"values": [1, 2]}),
    ("key-title", {"text": "La courbe de l'oubli", "accent": "l'oubli"}),
    ("key-title", {"text": "La courbe de l'oubli", "accent": "L'OUBLI"}),
    ("key-title", {"text": "Une lumière blanche, un ciel bleu", "accent": "ciel bleu"}),
    ("key-title", {"text": "Une lumière blanche, un ciel bleu", "accent": "blanche"}),
    ("key-title", {"text": "Pourquoi on oublie"}),
])
def test_check_props_accepts_matching_labels_and_accent(kind, props):
    assert scene_schema.check_props(kind, props, "S") == []


@pytest.mark.parametrize("el", ["chips.<i>", "values.<i>", "labels.<i>"])
def test_check_el_refuses_literal_patterns(el):
    kind = "fact-chips" if el.startswith("chips") else "shape-diagram"
    props = {"chips": ["a"], "values": [1], "labels": ["a"]}
    assert scene_schema.check_el(kind, props, el, "S")


def test_check_el_names_the_valid_range():
    props = {"values": [1, 2, 3], "labels": ["a", "b"]}
    assert scene_schema.check_el("shape-diagram", props, "values.2", "S") == []
    assert scene_schema.check_el("shape-diagram", props, "values.3", "S") == [
        "S : « el » « values.3 » invalide pour « shape-diagram ». Chemins acceptés : values.0 à values.2, labels.0 à labels.1."
    ]
    assert scene_schema.check_el("key-title", {"text": "x"}, "title", "S") == [
        "S : « el » « title » invalide pour « key-title ». Chemins acceptés : text, accent."
    ]
    assert scene_schema.check_el("person-card", {"name": "x"}, None, "S")


def test_plan_check_reports_props_and_el_errors(job_with_fixtures):
    plan = json.loads((job_with_fixtures / "plan.json").read_text(encoding="utf-8"))
    plan["parts"][0]["scenes"][0]["props"] = {"title": "Pourquoi on oublie"}
    plan["parts"][0]["scenes"][1]["items"][1]["el"] = "values.9"
    (job_with_fixtures / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    errors = plan_check.check_plan(job_with_fixtures)
    assert "Partie 1, scène 1 : prop inconnue « title » pour « key-title ». Props acceptées : text, accent." in errors
    assert "Partie 1, scène 1 : prop « text » manquante pour « key-title ». Props acceptées : text, accent." in errors
    assert any(e.startswith("Partie 1, scène 2 : « el » « values.9 »") and "values.0 à values.3" in e for e in errors)


def test_plan_check_requires_el(job_with_fixtures):
    plan = json.loads((job_with_fixtures / "plan.json").read_text(encoding="utf-8"))
    del plan["parts"][0]["scenes"][1]["items"][0]["el"]
    (job_with_fixtures / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    assert any("« el »" in e for e in plan_check.check_plan(job_with_fixtures))
