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
    assert re.fullmatch(r"- \[\d{4}-\d{2}-\d{2}\] \(ZcOLpOS-QcY\) Le rendu coupe le texte long\.", lines(path)[0])
    learn.add_bug("Sans job.")
    assert lines(path)[1].endswith("] Sans job.")


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
    assert "(" not in lines(home / "retours.md")[0].split("] ", 1)[1].split(" ")[0]


def test_cli_learn_usage_errors(capsys):
    assert cli.main(["learn"]) == 1
    assert cli.main(["learn", "--bug"]) == 1
    assert cli.main(["learn", "a", "b"]) == 1
