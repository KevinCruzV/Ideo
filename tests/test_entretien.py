import pytest

from ideo import cli, common, entretien, history, learn, retours


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    return tmp_path


def produce_times(n):
    for i in range(n):
        history.record_produce(f"job{i}", 60.0)


def test_nothing_is_due_at_the_start():
    assert entretien.notice() is None


def test_due_when_the_threshold_of_videos_is_reached():
    produce_times(4)
    assert entretien.notice() is None
    produce_times(1)
    assert entretien.notice() == "Entretien à lancer : 5 vidéos depuis le dernier entretien."


def test_due_when_eight_entries_are_open():
    for i in range(7):
        retours.add(retours.SIGNALES, f"défaut {i}")
    assert entretien.notice() is None
    retours.add_wish("un dessin")
    assert entretien.notice() == "Entretien à lancer : 8 retours non traités."


def test_both_reasons_are_joined():
    produce_times(5)
    for i in range(8):
        retours.add(retours.SIGNALES, f"défaut {i}")
    assert entretien.notice() == ("Entretien à lancer : 5 vidéos depuis le dernier entretien et 8 retours non traités.")


def test_advice_only_when_auto_is_off(home):
    (home / "config.json").write_text('{"entretien_auto": false}', encoding="utf-8")
    produce_times(5)
    assert entretien.notice() == "Entretien conseillé : 5 vidéos depuis le dernier entretien."


def test_threshold_is_configurable(home):
    (home / "config.json").write_text('{"entretien_seuil": 2}', encoding="utf-8")
    produce_times(2)
    assert entretien.notice().startswith("Entretien à lancer : 2 vidéos")


def test_done_or_failed_resets_the_video_counter():
    produce_times(6)
    history.entretien_failed("tests rouges")
    assert entretien.notice() is None


def test_report_file_and_line(home):
    produce_times(2)
    history.add_errors("jobA", {"survol": 1})
    history.add_errors("jobB", {"survol": 1, "silence-long": 1})
    retours.add(retours.SIGNALES, "le rendu coupe")
    retours.add_detected("silence-long", "jobB", "un silence")
    retours.add_wish("drapeau")
    retours.add_wish("Drapeau")
    retours.add_wish("carte")
    learn.add_lesson("Garde moins d'événements dans la vidéo.")
    learn.add_lesson("Garde moins d'événements dans la vidéo entière.")
    line = entretien.report_line()
    assert line == (f"OK entretien : {home / 'entretien.md'} (2 vidéos depuis le dernier entretien, 2 défauts, "
                    "2 dessins manquants, 2 leçons)")
    text = (home / "entretien.md").read_text(encoding="utf-8")
    assert "- survol : 2 job(s)" in text and "- silence-long : 1 job(s)" in text
    assert text.index("Drapeau (×2)") < text.index("- carte") if "Drapeau (×2)" in text else text.index("drapeau (×2)") < text.index("- carte")
    assert "le rendu coupe" in text and "## Doublons probables" in text
    assert "Garde moins d'événements dans la vidéo." in text.split("## Doublons probables")[1]


def test_no_duplicate_for_different_lessons(home):
    learn.add_lesson("Mets un kicker sur chaque changement de lieu.")
    learn.add_lesson("Finis toujours par la réponse à l'accroche.")
    entretien.report_line()
    assert "- aucun" in (home / "entretien.md").read_text(encoding="utf-8").split("## Doublons probables")[1]


def test_cli_entretien_prints_the_report_line(home, capsys):
    assert cli.main(["entretien"]) == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("OK entretien : ") and out.endswith("(0 vidéos depuis le dernier entretien, 0 défauts, 0 dessins manquants, 0 leçons)")
    assert (home / "entretien.md").exists()


def test_cli_fait_records_and_prepare_shows_it_once(home, capsys):
    produce_times(5)
    assert cli.main(["entretien", "--fait", "2 défauts corrigés, 1 dessin ajouté"]) == 0
    assert capsys.readouterr().out.startswith("OK entretien : ")
    assert history.videos_since() == 0
    assert history.take_notice().endswith(", 2 défauts corrigés, 1 dessin ajouté.")


def test_cli_fait_without_summary_is_accepted(capsys):
    assert cli.main(["entretien", "--fait"]) == 0


def test_cli_echec_needs_a_reason_and_records_it(capsys):
    assert cli.main(["entretien", "--echec"]) == 1
    assert cli.main(["entretien", "--echec", "dépôt modifié"]) == 0
    assert history.take_notice() == "Dernier entretien : échec, dépôt modifié."


def test_cli_entretien_usage_errors(capsys):
    assert cli.main(["entretien", "--autre"]) == 1
    assert cli.main(["entretien", "--fait", "a", "b"]) == 1
