import json

import pytest

from ideo import plan_check

EM = chr(0x2014)


def load(job):
    return json.loads((job / "plan.json").read_text(encoding="utf-8"))


def write(job, plan):
    (job / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")


def test_valid_plan_has_no_errors(job_with_fixtures):
    assert plan_check.check_plan(job_with_fixtures) == []
    assert (job_with_fixtures / "plan.md").exists()


def test_plan_md_lists_scenes_and_source_clips(job_with_fixtures):
    plan_check.check_plan(job_with_fixtures)
    md = (job_with_fixtures / "plan.md").read_text(encoding="utf-8")
    assert "L'oubli" in md
    assert "- [shape-diagram] Le lundi tout est clair" in md
    assert "0:26" in md and "1:10" in md


def test_invalid_plan_writes_no_plan_md(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["lang"] = "de"
    write(job_with_fixtures, plan)
    plan_check.check_plan(job_with_fixtures)
    assert not (job_with_fixtures / "plan.md").exists()


@pytest.mark.parametrize("mutate,fragment", [
    (lambda p: p["parts"][0]["scenes"][1]["items"].append({"el": "x", "on": "absent"}), "« absent » n'est pas dans le texte"),
    (lambda p: p["parts"].extend([dict(p["parts"][0], n=i) for i in range(2, 10)]), "8 parties au maximum"),
    (lambda p: p["parts"][0].update(hook="Pourquoi " + EM + " vraiment ?"), "tiret cadratin"),
    (lambda p: p["parts"][0]["scenes"][0].update(type="carousel"), "type inconnu"),
    (lambda p: p.update(lang="de"), "langue"),
    (lambda p: p.update(version=2), "version"),
    (lambda p: p["parts"][0].update(n=3), "numéro"),
    (lambda p: p["parts"][0].update(hook=" "), "accroche"),
    (lambda p: p["parts"][0]["scenes"][1].update(src="99:00"), "durée de la vidéo"),
    (lambda p: p["parts"][0]["scenes"][1].update(src="abc"), "minutage invalide"),
    (lambda p: p["parts"][0]["scenes"][2].update(sfx="5:55"), "sfx.json"),
    (lambda p: p["parts"][0]["scenes"][0]["props"].update(title="a " + EM + " b"), "tiret cadratin"),
    (lambda p: p["parts"][0]["scenes"][0].pop("say"), "say"),
    (lambda p: p.update(parts=[]), "au moins 1 partie"),
    (lambda p: p.update(parts="x"), "liste"),
    (lambda p: p["parts"][0].update(scenes=[]), "scène"),
])
def test_plan_errors(job_with_fixtures, mutate, fragment):
    plan = load(job_with_fixtures)
    mutate(plan)
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any(fragment in e for e in errors), errors


def test_errors_start_with_a_location(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][0]["type"] = "carousel"
    plan["lang"] = "de"
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert len(errors) >= 2
    assert any(e.startswith("Partie 1, scène 1 : ") for e in errors)
    assert any(e.startswith("Plan : ") for e in errors)


def test_quote_not_found_points_to_closest_passage(job_with_fixtures):
    plan = load(job_with_fixtures)
    quote = plan["parts"][0]["scenes"][4]
    quote["props"]["text"] = "Nous oublions la plupart de ce que nous retenons en moins d'une semaine"
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    hit = [e for e in errors if "citation" in e]
    assert hit and hit[0].startswith("Partie 1, scène 5 : ")
    assert "[0:26]" in hit[0]


def test_quote_far_from_src_is_not_found(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][4]["src"] = "1:59"
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("citation" in e and "[0:26]" in e for e in errors), errors


def test_quote_without_src_is_an_error(job_with_fixtures):
    plan = load(job_with_fixtures)
    del plan["parts"][0]["scenes"][4]["src"]
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("src" in e and "citation" in e for e in errors), errors


def test_part_too_short_reports_estimate(job_with_fixtures):
    plan = load(job_with_fixtures)
    for scene in plan["parts"][0]["scenes"]:
        scene["say"] = "Court lundi jeudi."
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    short = [e for e in errors if "trop courte" in e]
    assert short and short[0].startswith("Partie 1 : ")
    assert "Ajoute" in short[0] and " s" in short[0]


def test_part_too_long_reports_estimate(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][0]["say"] = "mot " * 120
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    long = [e for e in errors if "trop longue" in e]
    assert long and "coupe" in long[0]


def test_estimate_seconds():
    assert plan_check.estimate_seconds("un deux trois quatre cinq", "fr") == pytest.approx(5 / 2.6)
    assert plan_check.estimate_seconds("un deux trois quatre cinq", "en") == pytest.approx(5 / 2.8)
    assert plan_check.estimate_seconds("un deux", "es") == pytest.approx(2 / 2.6)


def test_missing_plan_json_is_an_error_not_a_traceback(job_with_fixtures):
    (job_with_fixtures / "plan.json").unlink()
    errors = plan_check.check_plan(job_with_fixtures)
    assert errors and errors[0].startswith("Plan : ") and "plan.json" in errors[0]


def test_invalid_json_is_an_error(job_with_fixtures):
    (job_with_fixtures / "plan.json").write_text("{pas du json", encoding="utf-8")
    errors = plan_check.check_plan(job_with_fixtures)
    assert errors and "JSON" in errors[0]


def test_wrong_types_never_raise(job_with_fixtures):
    for bad in ([], 3, {"version": 1, "lang": "fr", "parts": [5]},
                {"version": 1, "lang": "fr", "parts": [{"n": 1, "hook": "x", "scenes": [7, {"type": 3, "say": None, "props": [], "items": "z"}]}]}):
        write(job_with_fixtures, bad)
        errors = plan_check.check_plan(job_with_fixtures)
        assert errors and all(isinstance(e, str) for e in errors)
