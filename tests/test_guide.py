import json
import re
import shutil
from pathlib import Path

import pytest

from ideo import plan_check

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
    assert types.count("key-title") <= 2 and types.count("mascot") <= 1
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
        words = scene["say"].split()
        for item in scene.get("items", []):
            assert plan_check.find_span(words, item["on"]) is not None, item


def test_no_em_dash_in_task_files():
    for name in OWN_FILES:
        assert EM_DASH not in (REPO / name).read_text(encoding="utf-8"), name
