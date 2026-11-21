import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import json
import shutil

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def job_with_fixtures(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    shutil.copy(FIXTURES / "words_small.json", job / "words.json")
    shutil.copy(FIXTURES / "plan_ok.json", job / "plan.json")
    (job / "lang.txt").write_text("fr", encoding="utf-8")
    (job / "sfx.json").write_text(
        json.dumps([{"at": "1:10", "s": 70.0, "e": 72.5}]), encoding="utf-8"
    )
    (job / "info.json").write_text(json.dumps({"duration": 120}), encoding="utf-8")
    return job
