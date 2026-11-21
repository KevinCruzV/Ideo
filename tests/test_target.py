import json

import pytest

from ideo import target


def test_useful_seconds_merges_overlapping_ranges():
    assert target.useful_seconds(1000, [(100, 200), (150, 250), (900, 2000)]) == pytest.approx(1000 - 150 - 100)


def test_useful_seconds_without_ranges():
    assert target.useful_seconds(600, []) == 600


@pytest.mark.parametrize("useful,expected", [
    (30, (45, 100)), (239, (45, 100)), (240, (90, 150)), (599, (90, 150)), (600, (120, 180)), (3000, (120, 180)),
])
def test_bounds_by_useful_source_duration(useful, expected):
    assert target.bounds(useful) == expected


def test_words_use_the_rate_of_the_language():
    assert target.words(100, 180, "fr") == (260, 468)
    assert target.words(100, 180, "en") == (280, 504)
    assert target.words(100, 180, "es") == (260, 468)


def test_line_text():
    line = target.line(1553, [], "fr")
    assert line == ("Durée conseillée : 120 à 180 s (environ 312 à 468 mots de say). "
                    "Plus court si l'histoire tient, jusqu'à 300 s si elle en a besoin.")


def test_for_job_subtracts_sponsor_and_end_ranges(tmp_path):
    (tmp_path / "info.json").write_text(json.dumps({"duration": 700}), encoding="utf-8")
    (tmp_path / "skip.json").write_text(json.dumps({"hidden": [{"s": 0, "e": 150}], "segments": []}), encoding="utf-8")
    (tmp_path / "lang.txt").write_text("en", encoding="utf-8")
    assert target.for_job(tmp_path) == "Durée conseillée : 90 à 150 s (environ 252 à 420 mots de say). " \
        "Plus court si l'histoire tient, jusqu'à 300 s si elle en a besoin."


def test_for_job_without_duration_is_none(tmp_path):
    assert target.for_job(tmp_path) is None
