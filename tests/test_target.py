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
    assert target.words(100, 180, "fr") == (340, 612)
    assert target.words(100, 180, "en") == (360, 648)
    assert target.words(100, 180, "es") == (340, 612)


def test_line_text():
    line = target.line(1553, [], "fr")
    assert line == ("Durée conseillée : 120 à 180 s (environ 408 à 612 mots de say). "
                    "Plus court si l'histoire tient, jusqu'à 300 s si elle en a besoin.")


def test_for_job_subtracts_sponsor_and_end_ranges(tmp_path):
    (tmp_path / "info.json").write_text(json.dumps({"duration": 700}), encoding="utf-8")
    (tmp_path / "skip.json").write_text(json.dumps({"hidden": [{"s": 0, "e": 150}], "segments": []}), encoding="utf-8")
    (tmp_path / "lang.txt").write_text("en", encoding="utf-8")
    assert target.for_job(tmp_path) == "Durée conseillée : 90 à 150 s (environ 324 à 540 mots de say). " \
        "Plus court si l'histoire tient, jusqu'à 300 s si elle en a besoin."


def test_for_job_without_duration_is_none(tmp_path):
    assert target.for_job(tmp_path) is None


def test_one_speech_rate_feeds_the_header_and_the_estimate():
    from ideo import plan_check, speed

    assert speed.rate("fr") == 3.4 and speed.rate("en") == 3.6 and speed.rate("de") == speed.DEFAULT
    assert plan_check.estimate_seconds("a b c d e f", "en") == pytest.approx(6 / speed.rate("en"))
    assert target.words(100, 100, "en")[0] == round(100 * speed.rate("en"))
