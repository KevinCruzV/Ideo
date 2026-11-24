import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from ideo import common, plan_check, scene_schema

REPO = Path(__file__).resolve().parent.parent
GUIDE = REPO / "skills" / "ideo" / "references" / "plan-guide.md"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "guide"
EM_DASH = chr(0x2014)
OWN_FILES = [
    "skills/ideo/SKILL.md",
    "skills/ideo/references/plan-guide.md",
    "skills/setup/SKILL.md",
    "README.md",
    "ideo/cli.py",
    "ideo/pipeline.py",
    "ideo/__main__.py",
    "tests/test_cli.py",
    "tests/test_guide.py",
    "tests/fixtures/guide/plan.json",
    "tests/fixtures/guide/transcript_compact.md",
]


def guide_example() -> dict:
    text = GUIDE.read_text(encoding="utf-8")
    section = text.split("## 9. Exemple complet", 1)[1]
    block = re.search(r"```json\n(.*?)\n```", section, re.S).group(1)
    return json.loads(block)


@pytest.fixture
def guide_job(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    for name in ("words.json", "sfx.json", "info.json", "lang.txt", "transcript_compact.md"):
        shutil.copy(FIXTURE / name, job / name)
    (job / "plan.json").write_text(json.dumps(guide_example(), ensure_ascii=False), encoding="utf-8")
    return job


def test_guide_example_validates_with_zero_errors(guide_job):
    assert plan_check.check_plan(guide_job) == []


def test_guide_example_is_the_committed_fixture_plan():
    assert guide_example() == json.loads((FIXTURE / "plan.json").read_text(encoding="utf-8"))


def test_guide_example_src_are_paragraph_markers():
    transcript = (FIXTURE / "transcript_compact.md").read_text(encoding="utf-8")
    markers = set(re.findall(r"^\[(\d+:\d\d)\]", transcript, re.M))
    sounds = set(re.findall(r"^\[son (\d+:\d\d) ", transcript, re.M))
    for scene in guide_example()["parts"][0]["scenes"]:
        assert scene["src"] in markers
        if "sfx" in scene:
            assert scene["sfx"] in sounds


def test_guide_example_follows_its_own_variety_rules():
    part = guide_example()["parts"][0]
    types = [s["type"] for s in part["scenes"]]
    assert 8 <= len(types) <= 25
    assert all(a != b for a, b in zip(types, types[1:]))
    assert types.count("key-title") <= 2 and types.count("mascot") <= 3
    anchors = [i for i, t in enumerate(types) if t in ("quote", "object-state")]
    assert anchors and anchors[0] < 6
    assert all(b - a <= 6 for a, b in zip(anchors, anchors[1:]))
    assert 6 <= len(part["hook"].split()) <= 10


def test_guide_per_type_examples_cover_the_twelve_types():
    text = GUIDE.read_text(encoding="utf-8")
    section = text.split("Un exemple par type :", 1)[1].split("## 6.", 1)[0]
    block = re.search(r"```json\n(.*?)\n```", section, re.S).group(1)
    scenes = [json.loads(line) for line in block.splitlines()]
    assert sorted(s["type"] for s in scenes) == sorted(plan_check.SCENE_TYPES)
    for scene in scenes:
        assert scene_schema.check_props(scene["type"], scene["props"], "x") == []
        for item in scene.get("items", []):
            assert scene_schema.check_el(scene["type"], scene["props"], item["el"], "x") == []
        words = scene["say"].split()
        for item in scene.get("items", []):
            assert plan_check.find_span(words, item["on"]) is not None, item


SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def per_type_examples() -> list[dict]:
    text = GUIDE.read_text(encoding="utf-8")
    section = text.split("Un exemple par type :", 1)[1].split("## 6.", 1)[0]
    block = re.search(r"```json\n(.*?)\n```", section, re.S).group(1)
    return [json.loads(line) for line in block.splitlines()]


def all_example_scenes() -> list[dict]:
    return guide_example()["parts"][0]["scenes"] + per_type_examples()


@pytest.mark.parametrize("scene", all_example_scenes(), ids=lambda s: s["type"] + ":" + s["src"])
def test_first_item_is_in_the_first_sentence(scene):
    first = SENTENCE_END.split(scene["say"])[0]
    assert plan_check.find_span(first.split(), scene["items"][0]["on"]) is not None, (first, scene["items"][0])


@pytest.mark.parametrize("scene", all_example_scenes(), ids=lambda s: s["type"] + ":" + s["src"])
def test_items_are_in_spoken_order(scene):
    words = scene["say"].split()
    starts = [plan_check.find_span(words, item["on"])[0] for item in scene["items"]]
    assert starts == sorted(starts), scene["items"]


def test_guide_and_skill_say_the_title_is_free():
    text = GUIDE.read_text(encoding="utf-8")
    assert "ni le titre de la vidéo (lignes" not in text
    assert "Le sujet et les mots de la ligne `Titre :` sont libres" in text


def test_no_em_dash_in_task_files():
    for name in OWN_FILES:
        assert EM_DASH not in (REPO / name).read_text(encoding="utf-8"), name


def tracked_text_files():
    names = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True).stdout.split(b"\0")
    for name in filter(None, names):
        path = REPO / name.decode("utf-8")
        if not path.is_file():
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue


def test_no_em_dash_in_any_tracked_file():
    hits = [str(path.relative_to(REPO)) for path, text in tracked_text_files() if EM_DASH in text]
    assert hits == []


def test_guide_and_skill_document_mood_and_photo():
    guide = (common.REPO_ROOT / "skills" / "ideo" / "references" / "plan-guide.md").read_text(encoding="utf-8")
    skill = (common.REPO_ROOT / "skills" / "ideo" / "SKILL.md").read_text(encoding="utf-8")
    assert '"mood": "dark"' in guide and '"mood": "dark"' in skill
    assert 'ideo photo JOB' in guide and "ideo photo JOB" in skill and "aucune photo libre" in guide and "aucune photo libre" in skill
    assert "par acte" in guide and "par acte" in skill


def test_skill_writing_guard_names_only_signs_that_check_really_prints():
    from ideo import slop

    skill = (common.REPO_ROOT / "skills" / "ideo" / "SKILL.md").read_text(encoding="utf-8")
    guard = skill.split("Garde d'écriture", 1)[1].split("Relecture :", 1)[0]
    labels = [label for label, _ in slop.MESSAGES.values()]
    assert all(label in guard for label in labels)
    plan_check_source = (REPO / "ideo" / "plan_check.py").read_text(encoding="utf-8")
    slop_source = (REPO / "ideo" / "slop.py").read_text(encoding="utf-8")
    for sign in ("recopie la vidéo d'origine mot pour mot", "reprend des suites de {COPY_GRAM} mots", "tiret cadratin"):
        assert sign in plan_check_source
    assert "reprend des suites de 5 mots" in guard and "recopie la vidéo d'origine mot pour mot" in guard
    assert "formule « ce n'est pas X" in guard and "formule « ce n'est pas X, c'est Y »" in slop_source
    assert "trois phrases de trois mots" in guard and "trois phrases de trois mots ou moins" in slop_source
    assert "modèle `opus`" in guard and "Un seul sous-agent Opus par plan" in guard
