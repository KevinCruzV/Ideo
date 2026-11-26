import json

import pytest

from ideo import history


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    return tmp_path


def test_one_entry_per_job_with_its_facts():
    history.note_plan("jobs/abc", lang="fr", source=1553, scenes=12)
    history.note_plan("jobs/abc", lang="fr", source=1553, scenes=14)
    data = history.load()
    entry = data["jobs"]["abc"]
    assert entry["id"] == "abc" and entry["lang"] == "fr" and entry["source"] == 1553 and entry["scenes"] == 14
    assert len(entry["date"]) == 10 and list(data["jobs"]) == ["abc"]


def test_errors_accumulate_with_their_count():
    history.add_errors("abc", {"ancre-absente": 2})
    history.add_errors("abc", {"ancre-absente": 1, "texte-trop-long": 1})
    assert history.load()["jobs"]["abc"]["errors"] == {"ancre-absente": 3, "texte-trop-long": 1}


def test_relire_codes_are_kept_from_the_first_pass_only():
    history.add_relire("abc", ["survol", "sans-kicker"])
    history.add_relire("abc", ["liste-nue"])
    assert history.load()["jobs"]["abc"]["relire"] == ["survol", "sans-kicker"]


def test_qc_codes_and_produced_duration():
    history.add_qc("abc", ["silence-long", "scene-figee", "scene-figee"])
    history.record_produce("abc", 70.6)
    entry = history.load()["jobs"]["abc"]
    assert entry["qc"] == ["scene-figee", "silence-long"] and entry["produced"] == 70.6
    assert history.videos_since() == 1
    history.record_produce("abc", 71.0)
    assert history.videos_since() == 2


def test_missing_or_unreadable_file_means_empty_history(home):
    assert history.load()["jobs"] == {}
    (home / "historique.json").write_text("{pas du json", encoding="utf-8")
    assert history.load()["jobs"] == {}
    history.add_errors("abc", {"x": 1})
    assert history.load()["jobs"]["abc"]["errors"] == {"x": 1}


def test_wrong_shapes_never_raise(home):
    (home / "historique.json").write_text(json.dumps({"jobs": [1], "order": "x"}), encoding="utf-8")
    assert history.load()["jobs"] == {}
    (home / "historique.json").write_text("[]", encoding="utf-8")
    assert history.videos_since() == 0


def test_unwritable_location_never_raises(home):
    (home / "historique.json").mkdir()
    history.add_errors("abc", {"x": 1})
    history.record_produce("abc", 1.0)
    assert history.videos_since() == 0


def test_recent_codes_count_distinct_jobs_among_the_last_five():
    for i in range(6):
        history.add_errors(f"job{i}", {"vieux": 1} if i == 0 else {})
    history.add_errors("job5", {"frequent": 1})
    history.add_relire("job4", ["frequent"])
    history.add_qc("job3", ["frequent"])
    counts = history.recent_codes()
    assert counts["frequent"] == 3 and "vieux" not in counts


def test_touching_a_job_again_moves_it_to_the_last_five():
    for i in range(6):
        history.add_errors(f"job{i}", {"x": 1})
    history.add_errors("job0", {"x": 1})
    assert history.load()["order"][-1] == "job0" and len(history.recent_codes()) == 1


def test_entretien_done_resets_the_counter_and_shows_once():
    history.record_produce("a", 1.0)
    history.record_produce("b", 1.0)
    history.entretien_done("2 défauts corrigés")
    assert history.videos_since() == 0
    note = history.take_notice()
    assert note.startswith("Dernier entretien : ") and note.endswith(", 2 défauts corrigés.")
    assert history.take_notice() is None


def test_entretien_failure_resets_the_counter_and_shows_once():
    history.record_produce("a", 1.0)
    history.entretien_failed("tests rouges")
    assert history.videos_since() == 0
    assert history.take_notice() == "Dernier entretien : échec, tests rouges."
    assert history.take_notice() is None


def test_entretien_without_summary():
    history.entretien_done("")
    note = history.take_notice()
    assert note.startswith("Dernier entretien : 20") and note.endswith(".") and "None" not in note


def test_drawings_of_the_last_videos_are_counted_by_video():
    history.note_drawings("a", ["knife", "object:scale"])
    history.note_drawings("b", ["object:scale", "globe"])
    history.note_drawings("c", ["object:scale", "knife"])
    history.note_drawings("new", ["coin"])
    assert history.recent_drawings("new") == {"object:scale": 3, "knife": 2, "globe": 1}
    assert history.recent_drawings("new", videos=1) == {"object:scale": 1, "knife": 1}
    assert history.recent_drawings("c") == {"object:scale": 2, "coin": 1, "globe": 1, "knife": 1}


def test_drawings_are_replaced_on_a_second_check_and_never_raise(home):
    history.note_drawings("a", ["knife"])
    history.note_drawings("a", ["globe", "globe", 3])
    assert history.load()["jobs"]["a"]["drawings"] == ["globe"]
    (home / "historique.json").write_text("[]", encoding="utf-8")
    assert history.recent_drawings("a") == {}
