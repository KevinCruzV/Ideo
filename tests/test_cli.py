import sys

import pytest

from conftest import FakeBackend
from ideo import cli, common, compact, fetch, pipeline, render, transcribe, voice

INFO = {
    "id": "abcdefghijk",
    "title": "Mémoire et oubli",
    "channel": "Chaîne Test",
    "webpage_url": "https://www.youtube.com/watch?v=abcdefghijk",
    "duration": 120,
}


def lines(capsys):
    return capsys.readouterr().out.strip().splitlines()


@pytest.fixture
def produce_job(job_with_voice_fixtures, monkeypatch, fake_whisper):
    job = job_with_voice_fixtures
    common.save_json(job / "info.json", INFO)
    backend = FakeBackend()
    monkeypatch.setattr(voice, "get_backend", lambda log=None: backend)
    renders = []

    def fake_render(job_path, n):
        renders.append(n)
        plan = common.load_json(job_path / "plan.json")
        out = render.mp4_path(job_path, plan, n)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"mp4")
        common.mark(job_path, f"render-{n:02d}", True)
        return out

    monkeypatch.setattr(render, "render_part", fake_render)
    return job, backend, renders


def edit_first_say(job, text):
    plan = common.load_json(job / "plan.json")
    plan["parts"][0]["scenes"][0]["say"] = text
    common.save_json(job / "plan.json", plan)


def test_cli_prints_single_line(job_with_fixtures, capsys):
    assert cli.main(["status", str(job_with_fixtures)]) == 0
    out = lines(capsys)
    assert len(out) == 1 and out[0].startswith("OK status : ")


def test_cli_check_lists_errors_and_exits_1(job_with_fixtures, capsys):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["lang"] = "de"
    plan["parts"][0]["hook"] = ""
    common.save_json(job_with_fixtures / "plan.json", plan)
    assert cli.main(["check", str(job_with_fixtures)]) == 1
    out = lines(capsys)
    assert len(out) == 2
    assert all(line.startswith("ERREUR check : ") for line in out)


def test_cli_check_ok_gives_plan_md_path(job_with_fixtures, capsys):
    assert cli.main(["check", str(job_with_fixtures)]) == 0
    out = lines(capsys)
    assert len(out) == 1 and out[0].startswith("OK check : 1 vidéo")
    assert str((job_with_fixtures / "plan.md").resolve()) in out[0]


@pytest.mark.parametrize("cmd", ["check", "produce", "status", "deepen"])
def test_cli_never_raises_on_missing_job(tmp_path, monkeypatch, capsys, cmd):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    assert cli.main([cmd, str(tmp_path / "absent")]) == 1
    out = lines(capsys)
    assert len(out) == 1 and out[0].startswith(f"ERREUR {cmd} : ")


@pytest.mark.parametrize("argv", [[], ["fly"], ["check"], ["produce", "x", "--part"], ["produce", "x", "--part", "a"]])
def test_cli_usage_errors_are_one_line(argv, capsys):
    assert cli.main(argv) == 1
    out = lines(capsys)
    assert len(out) == 1 and out[0].startswith("ERREUR ")


def test_cli_accepts_bare_job_id(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    (tmp_path / "jobs" / "abcdefghijk").mkdir(parents=True)
    assert cli.main(["status", "abcdefghijk"]) == 0
    assert "prepare" in lines(capsys)[0]


def test_unexpected_exception_becomes_error_line(job_with_fixtures, monkeypatch, capsys):
    def boom(job):
        raise RuntimeError("panne interne")

    monkeypatch.setattr(pipeline, "status", boom)
    assert cli.main(["status", str(job_with_fixtures)]) == 1
    out = lines(capsys)
    assert len(out) == 1 and out[0].startswith("ERREUR status : ") and "panne interne" in out[0]
    log = (job_with_fixtures / "logs" / "cli.log").read_text(encoding="utf-8")
    assert "Traceback" in log and "RuntimeError" in log


def test_prepare_writes_progress_log_and_one_line(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    url = "https://www.youtube.com/watch?v=abcdefghijk"

    def noisy_fetch(u):
        print("bruit sur stdout")
        print("bruit sur stderr", file=sys.stderr)
        return common.job_dir(u)

    monkeypatch.setattr(fetch, "fetch", noisy_fetch)
    monkeypatch.setattr(transcribe, "transcribe", lambda job: [{"w": "a", "s": 0, "e": 1}] * 300)
    monkeypatch.setattr(compact, "prepare_transcript",
                        lambda job: {"words": 300, "paragraphs": 7, "sfx": 1, "lang": "fr"})
    assert cli.main(["prepare", url]) == 0
    captured = capsys.readouterr()
    out = captured.out.strip().splitlines()
    job = tmp_path / "jobs" / "abcdefghijk"
    assert len(out) == 1 and out[0].startswith("OK prepare : ")
    assert str(job.resolve()) in out[0] and "300 mots" in out[0]
    assert f"Transcription : {job.resolve() / 'transcript_compact.md'} (" in out[0]
    assert out[0].split(" Coût estimé : ")[1].startswith("lecture au moins ~")
    assert "bruit" not in captured.out and "bruit" not in captured.err
    progress = (job / "logs" / "progress.log").read_text(encoding="utf-8").splitlines()
    assert [line.split(" ")[2:4] for line in progress] == [["OK", "fetch"], ["OK", "transcribe"], ["OK", "transcript"]]


def test_prepare_bad_url_is_an_error_line(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    assert cli.main(["prepare", "https://example.com/video"]) == 1
    out = lines(capsys)
    assert len(out) == 1 and out[0].startswith("ERREUR prepare : URL YouTube non reconnue")


def test_produce_refuses_invalid_plan(produce_job, capsys):
    job, backend, renders = produce_job
    edit_first_say(job, "")
    assert cli.main(["produce", str(job)]) == 1
    out = lines(capsys)
    assert len(out) == 1 and "check" in out[0]
    assert backend.calls == [] and renders == []


def test_produce_outputs_and_progress(produce_job, capsys):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    out = lines(capsys)
    assert len(out) == 1 and out[0].startswith("OK produce : ")
    for name in ("video.mp4", "sources.md", "description.txt"):
        assert str((job / "out" / name).resolve()) in out[0]
    assert renders == [1]
    progress = (job / "logs" / "progress.log").read_text(encoding="utf-8")
    for step in ("voice-01", "assemble-01", "timeline-01", "render-01", "sources"):
        assert f"OK {step}" in progress
    assert (job / "parts" / "01" / "plan.hash").exists()


def test_produce_resumes_after_done_parts(produce_job, capsys):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    first = len(backend.calls)
    timeline_mtime = (job / "parts" / "01" / "timeline.json").stat().st_mtime
    assert cli.main(["produce", str(job)]) == 0
    assert len(backend.calls) == first
    assert renders == [1]
    assert (job / "parts" / "01" / "timeline.json").stat().st_mtime == timeline_mtime


def test_produce_invalidates_part_when_plan_changes(produce_job, capsys):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    first = len(backend.calls)
    edit_first_say(job, "Aujourd'hui nous allons voir pourquoi notre mémoire laisse filer presque tout ce que "
                        "nous venons de lire ou d'apprendre, en quelques jours à peine seulement.")
    assert cli.main(["produce", str(job)]) == 0
    assert len(backend.calls) == first + 7
    assert renders == [1, 1]
    assert "quelques jours à peine" in backend.calls[first + 1][0]


def test_src_edit_on_a_plain_scene_keeps_the_part(produce_job, capsys):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    first = len(backend.calls)
    plan = common.load_json(job / "plan.json")
    plan["parts"][0]["scenes"][3]["src"] = "0:36"
    common.save_json(job / "plan.json", plan)
    assert cli.main(["produce", str(job)]) == 0
    assert len(backend.calls) == first and renders == [1]


def test_quote_src_edit_redoes_the_part(produce_job, capsys):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    plan = common.load_json(job / "plan.json")
    assert plan["parts"][0]["scenes"][4]["type"] == "quote"
    plan["parts"][0]["scenes"][4]["src"] = "0:27"
    common.save_json(job / "plan.json", plan)
    assert cli.main(["produce", str(job)]) == 0
    assert renders == [1, 1]


def test_invalidation_deletes_stale_artifacts_and_marks(produce_job, monkeypatch, capsys):
    job, backend, renders = produce_job
    assert cli.main(["produce", str(job)]) == 0
    part_dir = job / "parts" / "01"
    edit_first_say(job, "Aujourd'hui nous allons voir pourquoi notre mémoire laisse filer presque tout ce que "
                        "nous venons de lire ou d'apprendre, en quelques jours à peine seulement.")

    def stop(job_path, n, backend=None):
        raise common.IdeoError("arrêt du test")

    monkeypatch.setattr(voice, "voice_part", stop)
    assert cli.main(["produce", str(job)]) == 1
    assert not list(part_dir.glob("seg_*"))
    for name in ("part.wav", "offsets.json", "timeline.json"):
        assert not (part_dir / name).exists()
    assert not (job / "out" / "video.mp4").exists()
    assert not (job / "out" / "description.txt").exists()
    steps = common.read_status(job)["steps"]
    assert not any(k in steps for k in ("voice-01", "assemble-01", "timeline-01", "render-01"))
    assert "ERREUR produce" in (job / "logs" / "progress.log").read_text(encoding="utf-8")


def test_produce_unknown_part(produce_job, capsys):
    job, _, _ = produce_job
    assert cli.main(["produce", str(job), "--part", "4"]) == 1
    assert "partie 4" in lines(capsys)[0]


def test_status_after_produce_says_done(produce_job, capsys):
    job, _, _ = produce_job
    common.mark(job, "fetch", True)
    common.mark(job, "transcribe", True)
    common.mark(job, "transcript", True)
    (job / "transcript_compact.md").write_text("x", encoding="utf-8")
    cli.main(["produce", str(job)])
    capsys.readouterr()
    assert cli.main(["status", str(job)]) == 0
    out = lines(capsys)
    assert len(out) == 1 and "produce" in out[0] and "rien" in out[0]


def test_status_after_plan_edit_asks_for_produce(produce_job, capsys):
    job, _, _ = produce_job
    for step in ("fetch", "transcribe", "transcript"):
        common.mark(job, step, True)
    (job / "transcript_compact.md").write_text("x", encoding="utf-8")
    cli.main(["produce", str(job)])
    edit_first_say(job, "Aujourd'hui nous allons voir pourquoi notre mémoire laisse filer presque tout ce que "
                        "nous venons de lire ou d'apprendre, en quelques jours à peine seulement.")
    cli.main(["check", str(job)])
    capsys.readouterr()
    cli.main(["status", str(job)])
    assert "suivant : produce (partie 1)" in lines(capsys)[0]


def test_status_steps_in_order(job_with_fixtures, capsys):
    job = job_with_fixtures
    (job / "plan.json").unlink()
    common.mark(job, "fetch", True)
    cli.main(["status", str(job)])
    assert "prepare" in lines(capsys)[0]
    common.mark(job, "transcribe", True)
    common.mark(job, "transcript", True)
    (job / "transcript_compact.md").write_text("x", encoding="utf-8")
    cli.main(["status", str(job)])
    assert "plan.json" in lines(capsys)[0]


def test_deepen_creates_sibling_job_sharing_prepared_files(job_with_fixtures, monkeypatch, capsys):
    root = job_with_fixtures.parent
    job = root / "abcdefghijk"
    job_with_fixtures.rename(job)
    (job / "transcript_compact.md").write_text("[0:02] Le matin", encoding="utf-8")
    (job / "skip.json").write_text("{}", encoding="utf-8")
    (job / "source.m4a").write_bytes(b"audio")
    for step in ("fetch", "transcribe", "transcript"):
        common.mark(job, step, True)
    assert cli.main(["deepen", str(job)]) == 0
    new = root / "abcdefghijk-2"
    out = lines(capsys)
    assert len(out) == 1 and str(new.resolve()) in out[0]
    for name in ("words.json", "lang.txt", "info.json", "sfx.json", "skip.json", "transcript_compact.md", "source.m4a"):
        assert (new / name).read_bytes() == (job / name).read_bytes()
    assert (new / "source.m4a").stat().st_ino == (job / "source.m4a").stat().st_ino
    for name in ("words.json", "skip.json", "transcript_compact.md"):
        assert (new / name).stat().st_ino != (job / name).stat().st_ino
    (new / "transcript_compact.md").write_text("autre", encoding="utf-8")
    assert (job / "transcript_compact.md").read_text(encoding="utf-8") == "[0:02] Le matin"
    assert not (new / "plan.json").exists()
    assert set(common.read_status(new)["steps"]) == {"fetch", "transcribe", "transcript"}
    assert cli.main(["deepen", str(job)]) == 0
    assert (root / "abcdefghijk-3").is_dir()


def test_deepen_needs_prepared_job(job_with_fixtures, capsys):
    assert cli.main(["deepen", str(job_with_fixtures)]) == 1
    assert "prepare" in lines(capsys)[0]


def test_prepare_refuses_a_language_without_voice(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    url = "https://www.youtube.com/watch?v=abcdefghijk"
    monkeypatch.setattr(fetch, "fetch", lambda u: common.job_dir(u))
    monkeypatch.setattr(transcribe, "transcribe", lambda job: [{"w": "a", "s": 0, "e": 1}] * 300)

    def fake_transcript(job):
        common.mark(job, "transcript", True)
        (job / "transcript_compact.md").write_text("x", encoding="utf-8")
        return {"words": 300, "paragraphs": 7, "sfx": 1, "lang": "sw"}

    monkeypatch.setattr(compact, "prepare_transcript", fake_transcript)
    for step in ("fetch", "transcribe"):
        common.mark(common.job_dir(url), step, True)
    assert cli.main(["prepare", url]) == 1
    out = lines(capsys)
    assert len(out) == 1 and out[0].startswith("ERREUR prepare : ") and "« sw »" in out[0]
    assert "Langues possibles : fr, en" in out[0]
    job = tmp_path / "jobs" / "abcdefghijk"
    assert not pipeline.prepared(job)
    assert cli.main(["status", str(job)]) == 0
    assert "« sw »" in lines(capsys)[0]
