import os
import time

from ideo import cli, common, config, pipeline, render, voice
from tests.test_cli import edit_first_say, produce_job
from tests.test_eleven import KEY, configure, server


def line(capsys):
    return capsys.readouterr().out.strip().splitlines()[0]


def go_paid(job, monkeypatch):
    configure({})
    config.mark_final(job)
    monkeypatch.setattr(voice, "retranscribe", lambda wav, lang, log=None: [])
    monkeypatch.setattr(voice.fidelity, "similarity", lambda a, b: 1.0)


def test_a_code_change_redoes_the_render_but_keeps_the_voice(produce_job, monkeypatch, capsys):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    calls = len(backend.calls)
    monkeypatch.setattr(pipeline, "code_version", lambda: "autre version du code")
    assert cli.main(["produce", str(job)]) == 0
    assert renders == [1, 1] and len(backend.calls) == calls


def test_the_same_code_and_plan_skip_everything(produce_job, capsys):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    calls = len(backend.calls)
    assert cli.main(["produce", str(job)]) == 0
    assert renders == [1] and len(backend.calls) == calls


def test_a_change_in_the_voice_code_redoes_a_free_voice(produce_job, monkeypatch):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    calls = len(backend.calls)
    monkeypatch.setattr(pipeline, "voice_code_version", lambda: "autre version de la voix")
    assert cli.main(["produce", str(job)]) == 0
    assert len(backend.calls) == calls + 7 and renders == [1, 1]


def test_a_change_in_the_voice_code_never_rebuys_a_paid_voice(produce_job, server, monkeypatch):
    job, _, renders = produce_job
    go_paid(job, monkeypatch)
    assert cli.main(["produce", str(job)]) == 0
    server.requests.clear()
    monkeypatch.setattr(pipeline, "voice_code_version", lambda: "autre version de la voix")
    monkeypatch.setattr(pipeline, "code_version", lambda: "autre version du code")
    assert cli.main(["produce", str(job)]) == 0
    assert server.requests == [] and renders == [1, 1]


def test_one_corrected_sentence_redoes_only_that_sentence_on_a_free_voice(produce_job):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    calls = len(backend.calls)
    edit_first_say(job, "Aujourd'hui nous allons voir pourquoi notre mémoire laisse filer presque tout ce que "
                        "nous venons de lire ou d'apprendre, en quelques jours à peine seulement.")
    assert cli.main(["produce", str(job)]) == 0
    assert len(backend.calls) == calls + 1 and "quelques jours à peine" in backend.calls[calls][0]
    assert renders == [1, 1]


def test_one_corrected_sentence_redoes_only_that_sentence_on_the_paid_voice(produce_job, server, monkeypatch):
    job, _, renders = produce_job
    go_paid(job, monkeypatch)
    assert cli.main(["produce", str(job)]) == 0
    first = len(server.requests)
    assert first >= 7
    edit_first_say(job, "Aujourd'hui nous allons voir pourquoi notre mémoire laisse filer presque tout ce que "
                        "nous venons de lire ou d'apprendre, en quelques jours à peine seulement.")
    assert cli.main(["produce", str(job)]) == 0
    assert len(server.requests) == first + 1 and "quelques jours à peine" in server.requests[first]["body"]["text"]
    assert renders == [1, 1]
    info = common.load_json(job / "parts" / "01" / "voice-info.json")
    assert info["engine"] == "elevenlabs" and info["characters"] > 0


def test_a_new_voice_setting_drops_the_old_voice(produce_job, monkeypatch):
    job, backend, _ = produce_job
    assert cli.main(["produce", str(job)]) == 0
    calls = len(backend.calls)
    monkeypatch.setattr(config, "rate", lambda: "+15%")
    assert cli.main(["produce", str(job)]) == 0
    assert len(backend.calls) == calls + 7


def test_removed_scenes_leave_no_stale_voice_files(produce_job):
    job, backend, _ = produce_job
    assert cli.main(["produce", str(job)]) == 0
    part_dir = job / "parts" / "01"
    (part_dir / "seg_42.wav").write_bytes(b"x")
    (part_dir / "seg_42.words.json").write_text("[]", encoding="utf-8")
    edit_first_say(job, "Aujourd'hui nous allons voir pourquoi notre mémoire laisse filer presque tout ce que "
                        "nous venons de lire ou d'apprendre, en quelques jours à peine seulement.")
    assert cli.main(["produce", str(job)]) == 0
    assert not (part_dir / "seg_42.wav").exists() and not (part_dir / "seg_42.words.json").exists()
    assert (part_dir / "seg_01.wav").exists()


def test_a_refused_payment_keeps_the_paid_voice(produce_job, server, monkeypatch, capsys):
    job, _, _ = produce_job
    go_paid(job, monkeypatch)
    assert cli.main(["produce", str(job)]) == 0
    capsys.readouterr()
    part_dir = job / "parts" / "01"
    before = sorted(p.name for p in part_dir.glob("seg_*"))
    assert before
    monkeypatch.setattr(voice, "PAID_LIMIT", 10)
    monkeypatch.setattr(pipeline, "voice_hash", lambda plan, job=None: "une autre voix")
    server.requests.clear()
    assert cli.main(["produce", str(job)]) == 1
    assert "--payer" in line(capsys)
    assert sorted(p.name for p in part_dir.glob("seg_*")) == before
    assert server.requests == []


def test_the_produce_line_says_the_video_is_new(produce_job, capsys):
    job, _, _ = produce_job
    assert cli.main(["produce", str(job)]) == 0
    text = line(capsys)
    assert " ; Version : vidéo refaite à " in text


def test_the_produce_line_says_when_nothing_changed(produce_job, capsys):
    job, _, _ = produce_job
    assert cli.main(["produce", str(job)]) == 0
    capsys.readouterr()
    assert cli.main(["produce", str(job)]) == 0
    text = line(capsys)
    assert " ; Version : AUCUNE nouvelle vidéo, celle-ci date de " in text and "rien n'a changé" in text


def test_the_produce_line_dates_an_old_video_with_its_day(produce_job, capsys):
    job, _, _ = produce_job
    assert cli.main(["produce", str(job)]) == 0
    capsys.readouterr()
    plan = common.load_json(job / "plan.json")
    old = time.time() - 3 * 86400
    os.utime(render.mp4_path(job, plan, 1), (old, old))
    assert cli.main(["produce", str(job)]) == 0
    text = line(capsys)
    assert " ; Version : AUCUNE nouvelle vidéo, celle-ci date du " in text and " à " in text


def test_an_old_free_job_without_voice_hash_gets_its_voice_redone(produce_job):
    job, backend, _ = produce_job
    assert cli.main(["produce", str(job)]) == 0
    (job / "parts" / "01" / "voice.hash").unlink()
    assert (job / "parts" / "01" / "voice-info.json").exists()
    calls = len(backend.calls)
    edit_first_say(job, "Aujourd'hui nous allons voir pourquoi notre mémoire laisse filer presque tout ce que "
                        "nous venons de lire ou d'apprendre, en quelques jours à peine seulement.")
    assert cli.main(["produce", str(job)]) == 0
    assert len(backend.calls) == calls + 7


def test_an_old_paid_job_without_voice_hash_keeps_its_paid_voice(produce_job, server, monkeypatch):
    job, _, _ = produce_job
    go_paid(job, monkeypatch)
    assert cli.main(["produce", str(job)]) == 0
    (job / "parts" / "01" / "voice.hash").unlink()
    first = len(server.requests)
    edit_first_say(job, "Aujourd'hui nous allons voir pourquoi notre mémoire laisse filer presque tout ce que "
                        "nous venons de lire ou d'apprendre, en quelques jours à peine seulement.")
    assert cli.main(["produce", str(job)]) == 0
    assert len(server.requests) == first + 1
