import re

import pytest

from ideo import cli, common, learn


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    return tmp_path


def lines(path):
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- [")]


def test_first_lesson_creates_the_file_with_a_title_and_a_dated_line():
    number, path = learn.add_lesson("Un kicker par changement de lieu.")
    assert number == 1 and path.name == "lecons.md"
    assert path.read_text(encoding="utf-8").startswith("# Leçons apprises")
    assert re.fullmatch(r"- \[\d{4}-\d{2}-\d{2}\] Un kicker par changement de lieu\.", lines(path)[0])


def test_lessons_are_appended_in_order():
    learn.add_lesson("Première règle.")
    number, path = learn.add_lesson("Deuxième règle.")
    assert number == 2 and [line.split("] ")[1] for line in lines(path)] == ["Première règle.", "Deuxième règle."]


@pytest.mark.parametrize("text,fragment", [
    ("", "vide"), ("   ", "vide"), ("x" * 201, "200"), ("Une règle " + chr(0x2014) + " avec tiret", "tiret cadratin"),
])
def test_refused_lessons(text, fragment):
    with pytest.raises(common.IdeoError, match=fragment):
        learn.add_lesson(text)
    assert not learn.lessons_path().exists()


def test_exactly_200_characters_is_accepted():
    assert learn.add_lesson("x" * 200)[0] == 1


def test_duplicate_ignores_case_and_punctuation():
    learn.add_lesson("Un kicker par lieu.")
    with pytest.raises(common.IdeoError, match="existe déjà"):
        learn.add_lesson("un KICKER, par lieu !")
    assert len(lines(learn.lessons_path())) == 1


def test_forty_lessons_at_most():
    for i in range(40):
        learn.add_lesson(f"Règle numéro {chr(97 + i % 26)}{chr(97 + i // 26)}.")
    with pytest.raises(common.IdeoError, match="fusionne ou retire"):
        learn.add_lesson("Une quarante et unième règle.")
    assert len(lines(learn.lessons_path())) == 40


def test_bug_goes_to_retours_not_to_lessons(home):
    path = learn.add_bug("Le rendu coupe le texte long.", "ZcOLpOS-QcY")
    assert path == home / "retours.md" and not learn.lessons_path().exists()
    assert re.fullmatch(r"- \[ \] \[\d{4}-\d{2}-\d{2}\] \(ZcOLpOS-QcY\) Le rendu coupe le texte long\.", lines(path)[0])
    learn.add_bug("Sans job.")
    assert lines(path)[1].endswith("] Sans job.")
    assert path.read_text(encoding="utf-8").index("## Défauts signalés") < path.read_text(encoding="utf-8").index("\n- [ ]")


def test_bug_refuses_empty_text():
    with pytest.raises(common.IdeoError):
        learn.add_bug("  ")


def test_cli_learn_prints_the_counter(capsys):
    assert cli.main(["learn", "Une règle utile."]) == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("OK learn : leçon 1/40 enregistrée dans ") and out.endswith("lecons.md")


def test_cli_learn_error_is_one_line(capsys):
    assert cli.main(["learn", ""]) == 1
    assert capsys.readouterr().out.startswith("ERREUR learn : ")


def test_cli_learn_bug_with_job(capsys, home):
    job = home / "jobs" / "abcdefghijk"
    job.mkdir(parents=True)
    assert cli.main(["learn", "--bug", "Un défaut de rendu", str(job)]) == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("OK learn : retour enregistré dans ") and out.endswith("retours.md")
    assert "(abcdefghijk)" in (home / "retours.md").read_text(encoding="utf-8")


def test_cli_learn_bug_without_job(capsys, home):
    assert cli.main(["learn", "--bug", "Un défaut"]) == 0
    assert "(" not in lines(home / "retours.md")[0].split("] ", 2)[2].split(" ")[0]


def test_cli_learn_usage_errors(capsys):
    assert cli.main(["learn"]) == 1
    assert cli.main(["learn", "--bug"]) == 1
    assert cli.main(["learn", "a", "b"]) == 1


def two_jobs_with(code, history_module):
    history_module.add_errors("jobA", {code: 1})
    history_module.add_errors("jobB", {code: 3})


def test_a_code_in_two_recent_jobs_adds_its_automatic_lesson():
    from ideo import history

    two_jobs_with("annee-sans-kicker", history)
    added = learn.auto_lessons()
    assert added == ["Dès qu'un say donne une année, mets cette date dans le kicker de la scène."]
    assert re.fullmatch(r"- \[\d{4}-\d{2}-\d{2}\] \(auto:annee-sans-kicker\) Dès qu'un say donne une année, mets cette date dans le kicker de la scène\.",
                        lines(learn.lessons_path())[0])


def test_a_code_in_one_job_only_adds_nothing():
    from ideo import history

    history.add_errors("jobA", {"annee-sans-kicker": 5})
    assert learn.auto_lessons() == [] and not learn.lessons_path().exists()


def test_the_automatic_lesson_is_added_only_once():
    from ideo import history

    two_jobs_with("survol", history)
    assert len(learn.auto_lessons()) == 1
    assert learn.auto_lessons() == []
    assert len(lines(learn.lessons_path())) == 1


def test_codes_without_a_phrase_add_nothing():
    from ideo import history

    two_jobs_with("silence-long", history)
    assert learn.auto_lessons() == [] and not learn.lessons_path().exists()


def test_no_more_than_twelve_automatic_lessons():
    from ideo import codes, history

    names = sorted(codes.LESSONS)[:15]
    for job in ("jobA", "jobB"):
        history.add_errors(job, {n: 1 for n in names})
    assert len(learn.auto_lessons()) == 12
    assert len(learn.auto_lessons()) == 0


def test_automatic_lessons_count_in_the_forty_cap():
    from ideo import history

    for i in range(40):
        learn.add_lesson(f"Règle numéro {chr(97 + i % 26)}{chr(97 + i // 26)}.")
    two_jobs_with("survol", history)
    assert learn.auto_lessons() == []


def test_every_table_lesson_fits_the_cap():
    from ideo import codes

    assert all(len(text) <= learn.MAX_LENGTH for text in codes.LESSONS.values())
