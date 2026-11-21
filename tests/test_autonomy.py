import json

import pytest

from ideo import cli, common, entretien, history, learn, retours
from tests.test_cli import produce_job


def out_lines(capsys):
    return capsys.readouterr().out.strip().splitlines()


def test_check_records_error_codes_and_counts(job_with_fixtures, capsys):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["parts"][0]["scenes"][0]["props"] = {"title": "x"}
    plan["parts"][0]["scenes"][1]["items"][0]["on"] = "absent"
    common.save_json(job_with_fixtures / "plan.json", plan)
    assert cli.main(["check", str(job_with_fixtures)]) == 1
    entry = history.load()["jobs"][job_with_fixtures.name]
    assert entry["errors"]["props-invalides"] == 2 and entry["errors"]["ancre-absente"] == 1


def test_check_records_job_facts_and_first_relire_codes(job_with_fixtures, capsys):
    assert cli.main(["check", str(job_with_fixtures)]) == 0
    entry = history.load()["jobs"][job_with_fixtures.name]
    assert entry["lang"] == "fr" and entry["source"] == 120 and entry["scenes"] == 5
    assert "sans-kicker" in entry["relire"]
    first = list(entry["relire"])
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["parts"][0]["scenes"][0]["props"]["kicker"] = "1885"
    common.save_json(job_with_fixtures / "plan.json", plan)
    cli.main(["check", str(job_with_fixtures)])
    assert history.load()["jobs"][job_with_fixtures.name]["relire"] == first


def test_check_never_fails_when_the_history_is_unusable(job_with_fixtures):
    (history.path()).mkdir()
    assert cli.main(["check", str(job_with_fixtures)]) == 0


def test_wishes_are_added_once_per_job_and_counted_across_jobs(job_with_fixtures, tmp_path, capsys):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["wishes"] = ["Drapeau américain", "carte du monde"]
    common.save_json(job_with_fixtures / "plan.json", plan)
    cli.main(["check", str(job_with_fixtures)])
    cli.main(["check", str(job_with_fixtures)])
    assert retours.wishes() == [("Drapeau américain", 1), ("carte du monde", 1)]
    history.new_wishes("autre-job", [])
    other = tmp_path / "autre-job"
    other.mkdir()
    for name in ("words.json", "plan.json", "lang.txt", "sfx.json", "info.json"):
        (other / name).write_bytes((job_with_fixtures / name).read_bytes())
    plan["wishes"] = ["drapeau americain"]
    common.save_json(other / "plan.json", plan)
    cli.main(["check", str(other)])
    assert retours.wishes()[0] == ("Drapeau américain", 2)


def test_invalid_plan_does_not_record_wishes(job_with_fixtures):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["wishes"] = ["a"] * 6
    common.save_json(job_with_fixtures / "plan.json", plan)
    assert cli.main(["check", str(job_with_fixtures)]) == 1
    assert retours.wishes() == []


def test_two_jobs_with_the_same_code_give_an_automatic_lesson_after_produce(produce_job, capsys):
    job = produce_job[0]
    history.add_relire("autre-job", ["sans-kicker"])
    cli.main(["check", str(job)])
    capsys.readouterr()
    assert cli.main(["produce", str(job)]) == 0
    line = out_lines(capsys)[0]
    lesson = "Mets un kicker (date, lieu ou acte) sur les scènes qui changent de moment ou de lieu."
    assert f" ; Leçon automatique : {lesson}" in line
    assert f"(auto:sans-kicker) {lesson}" in learn.lessons_path().read_text(encoding="utf-8")
    cli.main(["produce", str(job)])
    assert "Leçon automatique" not in out_lines(capsys)[0]


def test_one_job_alone_gives_no_automatic_lesson(produce_job, capsys):
    job = produce_job[0]
    cli.main(["check", str(job)])
    capsys.readouterr()
    cli.main(["produce", str(job)])
    assert "Leçon automatique" not in out_lines(capsys)[0]
    assert not learn.lessons_path().exists()


def test_produce_records_the_produced_duration_and_qc_codes(produce_job, capsys):
    job = produce_job[0]
    cli.main(["produce", str(job)])
    entry = history.load()["jobs"][job.name]
    assert entry["produced"] > 0 and isinstance(entry["qc"], list)
    assert history.videos_since() == 1


def test_code_originated_alerts_go_to_retours_once(produce_job, monkeypatch, capsys):
    from ideo import qc

    job = produce_job[0]
    monkeypatch.setattr(qc, "run_coded", lambda j, only=None: [("silence-long", "Partie 1 : un silence"),
                                                               ("scene-figee", "Partie 1 : figée")])
    cli.main(["produce", str(job)])
    cli.main(["produce", str(job)])
    detected = retours.unchecked(retours.DETECTES)
    assert [e.split("`")[1] for e in detected] == ["silence-long", "scene-figee"]
    assert learn.auto_lessons() == []
    assert not learn.lessons_path().exists()


def test_produce_adds_the_entretien_notice_at_the_threshold(produce_job, capsys):
    job = produce_job[0]
    for _ in range(4):
        cli.main(["produce", str(job)])
        assert "Entretien" not in out_lines(capsys)[0]
    cli.main(["produce", str(job)])
    assert out_lines(capsys)[0].endswith(" ; Entretien à lancer : 5 vidéos depuis le dernier entretien")


def test_produce_notice_is_advice_when_auto_is_off(produce_job, capsys):
    job = produce_job[0]
    (common._root() / "config.json").write_text(json.dumps({"entretien_auto": False, "entretien_seuil": 1}), encoding="utf-8")
    cli.main(["produce", str(job)])
    assert out_lines(capsys)[0].endswith(" ; Entretien conseillé : 1 vidéos depuis le dernier entretien")


def test_produce_notice_for_a_backlog(produce_job, capsys):
    job = produce_job[0]
    for i in range(8):
        retours.add(retours.SIGNALES, f"défaut {i}")
    cli.main(["produce", str(job)])
    assert out_lines(capsys)[0].endswith(" ; Entretien à lancer : 8 retours non traités")


def test_prepare_line_ends_with_the_last_entretien_once(tmp_path, monkeypatch, capsys):
    from ideo import compact, fetch, transcribe

    url = "https://www.youtube.com/watch?v=abcdefghijk"
    monkeypatch.setattr(fetch, "fetch", lambda u: common.job_dir(u))
    monkeypatch.setattr(transcribe, "transcribe", lambda job: [{"w": "a", "s": 0, "e": 1}] * 300)
    monkeypatch.setattr(compact, "prepare_transcript", lambda job: {"words": 300, "paragraphs": 7, "sfx": 1, "lang": "fr"})
    history.entretien_done("2 défauts corrigés")
    assert cli.main(["prepare", url]) == 0
    first = out_lines(capsys)[0]
    assert first.endswith(", 2 défauts corrigés.") and " Dernier entretien : 20" in first
    assert cli.main(["prepare", url]) == 0
    assert "Dernier entretien" not in out_lines(capsys)[0]


def test_prepare_line_after_a_failed_entretien(tmp_path, monkeypatch, capsys):
    from ideo import compact, fetch, transcribe

    url = "https://www.youtube.com/watch?v=abcdefghijk"
    monkeypatch.setattr(fetch, "fetch", lambda u: common.job_dir(u))
    monkeypatch.setattr(transcribe, "transcribe", lambda job: [{"w": "a", "s": 0, "e": 1}] * 300)
    monkeypatch.setattr(compact, "prepare_transcript", lambda job: {"words": 300, "paragraphs": 7, "sfx": 1, "lang": "fr"})
    history.entretien_failed("dépôt modifié")
    cli.main(["prepare", url])
    assert out_lines(capsys)[0].endswith(" Dernier entretien : échec, dépôt modifié.")


def test_produce_says_when_the_local_voice_is_not_installed(produce_job, monkeypatch, capsys):
    from ideo import config

    job = produce_job[0]
    monkeypatch.setattr(config, "apple_silicon", lambda: True)
    assert cli.main(["produce", str(job)]) == 0
    line = out_lines(capsys)[0]
    assert " ; Voix : voix en ligne, la voix locale n'est pas installée" in line
    assert line.index("Contrôle :") < line.index("Voix :")


def test_produce_says_nothing_about_the_voice_when_all_is_normal(produce_job, capsys):
    job = produce_job[0]
    cli.main(["produce", str(job)])
    assert "Voix :" not in out_lines(capsys)[0]


def test_produce_says_when_it_fell_back_to_the_online_voice(produce_job, monkeypatch, capsys):
    from ideo import voice

    job = produce_job[0]
    real = voice.voice_part

    def with_fallback(j, n, backend=None):
        paths = real(j, n, backend)
        common.save_json(j / "parts" / f"{n:02d}" / "voice-info.json",
                         {"engine": "edge", "fallback": "La commande a échoué (code 1)", "local_missing": False})
        return paths

    monkeypatch.setattr(voice, "voice_part", with_fallback)
    cli.main(["produce", str(job)])
    assert " ; Voix : repli sur la voix en ligne, La commande a échoué (code 1)" in out_lines(capsys)[0]


def test_produce_never_installs_the_local_voice(produce_job, monkeypatch, capsys):
    from ideo import config, setup_voix

    monkeypatch.setattr(config, "apple_silicon", lambda: True)
    monkeypatch.setattr(setup_voix, "run", lambda: (_ for _ in ()).throw(AssertionError("installation lancée")))
    assert cli.main(["produce", str(produce_job[0])]) == 0


def test_a_wish_for_an_existing_flag_becomes_a_relire_line_not_a_wish(job_with_fixtures, capsys):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["wishes"] = ["drapeau de la Chine", "carte du monde"]
    common.save_json(job_with_fixtures / "plan.json", plan)
    assert cli.main(["check", str(job_with_fixtures)]) == 0
    out = out_lines(capsys)
    assert "RELIRE : Plan : le drapeau de Chine existe : écris « flag:cn »" in out
    assert retours.wishes() == [("carte du monde", 1)]
    assert "drapeau-existe" in history.load()["jobs"][job_with_fixtures.name]["relire"]
    assert f", {len([x for x in out if x.startswith('RELIRE')])} point" in out[0]
    cli.main(["check", str(job_with_fixtures)])
    assert "le drapeau de Chine existe" not in "\n".join(out_lines(capsys))


def test_the_flag_wish_line_survives_the_review_off_switch(job_with_fixtures, capsys):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["wishes"] = ["drapeau Inde"]
    common.save_json(job_with_fixtures / "plan.json", plan)
    cli.main(["check", str(job_with_fixtures), "--sans-relecture"])
    out = out_lines(capsys)
    assert any("le drapeau de Inde existe : écris « flag:in »" in x for x in out) and retours.wishes() == []


def test_produce_says_once_when_no_music_is_found(produce_job, capsys):
    job = produce_job[0]
    assert cli.main(["produce", str(job)]) == 0
    line = out_lines(capsys)[0]
    assert line.count(" ; Musique : aucun morceau trouvé") == 1


def test_produce_is_silent_about_music_when_it_is_disabled_or_found(produce_job, capsys, tmp_path):
    job = produce_job[0]
    (common._root() / "config.json").write_text('{"music": false}', encoding="utf-8")
    cli.main(["produce", str(job)])
    assert "Musique" not in out_lines(capsys)[0]
    folder = tmp_path / "zik"
    folder.mkdir()
    from tests.test_music import tone_track

    tone_track(folder / "a.wav", seconds=8.0)
    (common._root() / "config.json").write_text(json.dumps({"music_dir": str(folder)}), encoding="utf-8")
    (job / "parts" / "01" / "music.json").unlink(missing_ok=True)
    cli.main(["produce", str(job)])
    assert "Musique" not in out_lines(capsys)[0]
