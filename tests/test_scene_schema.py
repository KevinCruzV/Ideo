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
    "object-state": "ObjectState", "shape-diagram": "ShapeDiagram", "mascot": "Mascot", "versus": "Versus",
}
SHARED = {"kicker": REPO / "render" / "src" / "scenes" / "SceneFrame.tsx"}
SHORT = REPO / "render" / "src" / "Short.tsx"


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
    assert "<SceneFrame" in SHORT.read_text(encoding="utf-8")
    for shared, path in SHARED.items():
        if re.search(rf"props\.{shared}\b", path.read_text(encoding="utf-8")):
            read.add(shared)
    schema = scene_schema.SCHEMA[kind]
    assert read == set(schema["required"]) | set(schema["optional"])


@pytest.mark.parametrize("kind", sorted(COMPONENTS))
def test_guide_table_lists_schema_props(kind):
    row = next(line for line in GUIDE.read_text(encoding="utf-8").splitlines() if line.startswith(f"| `{kind}` |"))
    props_cell = row.split("|")[3]
    for prop in list(scene_schema.SCHEMA[kind]["required"]) + list(scene_schema.SCHEMA[kind]["optional"]):
        assert f"`{prop}`" in props_cell


@pytest.mark.parametrize("kind,props,fragment", [
    ("key-title", {"title": "x"}, "prop inconnue « title » pour « key-title ». Props acceptées : text, accent, kicker, picto."),
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
    assert "Partie 1, scène 1 : prop inconnue « title » pour « key-title ». Props acceptées : text, accent, kicker, picto." in errors
    assert "Partie 1, scène 1 : prop « text » manquante pour « key-title ». Props acceptées : text, accent, kicker, picto." in errors
    assert any(e.startswith("Partie 1, scène 2 : « el » « values.9 »") and "values.0 à values.3" in e for e in errors)


def test_plan_check_requires_el(job_with_fixtures):
    plan = json.loads((job_with_fixtures / "plan.json").read_text(encoding="utf-8"))
    del plan["parts"][0]["scenes"][1]["items"][0]["el"]
    (job_with_fixtures / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    assert any("« el »" in e for e in plan_check.check_plan(job_with_fixtures))


CAPS_TEST = REPO / "render" / "src" / "text" / "caps.test.ts"


def ts_caps() -> dict:
    text = CAPS_TEST.read_text(encoding="utf-8")
    caps = {key: int(cap) for key, cap in re.findall(r'^\s+"?([\w.-]+)"?: \{\s*cap: (\d+)', text, re.M)}
    caps["title"] = int(re.search(r"TITLE_CAP = (\d+)", text).group(1))
    side = caps.pop("versus.side")
    caps["versus.left"] = caps["versus.right"] = side
    kicker = caps.pop("kicker")
    caps.update({f"{kind}.kicker": kicker for kind in scene_schema.SCHEMA})
    for kind, component in (("shape-diagram", "ShapeDiagram"), ("counter", "Counter")):
        source = (SCENES_DIR / f"{component}.tsx").read_text(encoding="utf-8")
        caps[f"{kind}.unit"] = int(re.search(r"props\.unit\)\.slice\(0, (\d+)\)", source).group(1))
    return caps


def test_caps_are_the_ones_proven_by_the_render_test():
    assert scene_schema.flat_caps() == ts_caps()


@pytest.mark.parametrize("kind,props,field,cap", [
    ("key-title", {"text": "x" * 91}, "props.text", 90),
    ("key-title", {"text": "un " + "x" * 41, "accent": "x" * 41}, "props.accent", 40),
    ("mascot", {"bubble": "x" * 81}, "props.bubble", 80),
    ("fact-chips", {"chips": ["court", "x" * 29]}, "props.chips.1", 28),
    ("stack-list", {"items": ["x" * 61]}, "props.items.0", 60),
    ("icon-grid", {"cells": [{"label": "a"}, {"label": "x" * 17}]}, "props.cells.1.label", 16),
    ("shape-diagram", {"values": [1, 2], "labels": ["a", "x" * 15]}, "props.labels.1", 14),
    ("stamp", {"text": "x" * 49}, "props.text", 48),
    ("person-card", {"name": "x" * 49}, "props.name", 48),
    ("person-card", {"name": "A", "role": "x" * 101}, "props.role", 100),
    ("counter", {"to": 3, "label": "x" * 61}, "props.label", 60),
    ("timeline", {"marks": [{"at": "x" * 13}]}, "props.marks.0.at", 12),
    ("timeline", {"marks": [{"at": 1990, "label": "x" * 49}]}, "props.marks.0.label", 48),
    ("timeline", {"marks": [{"at": 1}], "start": "x" * 31}, "props.start", 30),
    ("timeline", {"marks": [{"at": 1}], "end": "x" * 31}, "props.end", 30),
    ("quote", {"text": "x" * 201}, "props.text", 200),
    ("quote", {"text": "a", "speaker": "x" * 33}, "props.speaker", 32),
    ("object-state", {"object": "jar", "states": ["a", "x" * 37]}, "props.states.1", 36),
])
def test_each_cap_is_enforced_with_limit_and_count(kind, props, field, cap):
    errors = scene_schema.check_props(kind, props, "Partie 1, scène 2")
    assert len(errors) == 1, errors
    assert errors[0].startswith(f"Partie 1, scène 2 : « {field} » fait {cap + 1} caractères, {cap} au plus")
    assert "raccourcis" in errors[0]
    at_cap = json.loads(json.dumps(props).replace("x" * (cap + 1), "x" * cap))
    assert scene_schema.check_props(kind, at_cap, "x") == []


def test_wide_characters_count_double():
    assert scene_schema.screen_length("空気") == 4
    assert scene_schema.screen_length("abc") == 3
    errors = scene_schema.check_props("stamp", {"text": "空" * 25}, "x")
    assert errors and "50 caractères, 48 au plus" in errors[0]


def test_guide_type_table_lists_every_cap():
    text = GUIDE.read_text(encoding="utf-8")
    for key, cap in scene_schema.flat_caps().items():
        assert f"{cap} caractères" in text, key


def test_pictos_are_the_ones_the_render_library_draws():
    source = (REPO / "render" / "src" / "pictos" / "library.ts").read_text(encoding="utf-8")
    block = re.search(r"export const PICTOS = \[(.*?)\]", source, re.S).group(1)
    assert tuple(re.findall(r'"([\w-]+)"', block)) == scene_schema.PICTOS
