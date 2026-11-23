import json

from ideo import cli, common, config, eleven, pipeline, voice


def write(content):
    (common._root() / "config.json").write_text(json.dumps(content), encoding="utf-8")


def paid(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "cle-de-test")
    write({"engine": "elevenlabs"})


def test_a_draft_job_uses_the_free_voice_even_with_elevenlabs_configured(job_with_plan, monkeypatch):
    paid(monkeypatch)
    assert config.engine() == "elevenlabs"
    assert config.engine(job_with_plan) == "edge"
    monkeypatch.setattr(config, "kyutai_available", lambda: True)
    assert config.engine(job_with_plan) == "kyutai"


def test_finale_switches_the_job_to_the_configured_voice(job_with_plan, monkeypatch):
    paid(monkeypatch)
    assert not config.is_final(job_with_plan)
    config.mark_final(job_with_plan)
    assert config.is_final(job_with_plan) and config.engine(job_with_plan) == "elevenlabs"


def test_an_explicit_free_engine_stays_the_draft_voice(job_with_plan, monkeypatch):
    write({"engine": "edge"})
    monkeypatch.setattr(config, "kyutai_available", lambda: True)
    assert config.engine(job_with_plan) == "edge"


def test_the_backend_follows_the_job(job_with_plan, monkeypatch):
    paid(monkeypatch)
    log = job_with_plan / "logs" / "v.log"
    assert isinstance(voice.choose_backend("fr", log, job_with_plan), voice.EdgeTTSBackend)
    config.mark_final(job_with_plan)
    assert isinstance(voice.choose_backend("fr", log, job_with_plan), eleven.ElevenLabsBackend)


def test_going_final_redoes_the_part(job_with_plan, monkeypatch):
    paid(monkeypatch)
    plan = common.load_json(job_with_plan / "plan.json")
    part = plan["parts"][0]
    draft = pipeline.part_hash(plan, part, job_with_plan)
    config.mark_final(job_with_plan)
    assert pipeline.part_hash(plan, part, job_with_plan) != draft


def test_cli_finale_marks_the_job_and_gives_the_cost(job_with_plan, monkeypatch, capsys):
    paid(monkeypatch)
    assert cli.main(["finale", str(job_with_plan)]) == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("OK finale : ") and "caractères ElevenLabs" in out and "produce" in out
    assert config.is_final(job_with_plan)


def test_cli_finale_refuses_when_no_better_voice_is_configured(job_with_plan, capsys):
    write({})
    assert cli.main(["finale", str(job_with_plan)]) == 1
    assert capsys.readouterr().out.startswith("ERREUR finale : ")
    assert not config.is_final(job_with_plan)


def test_draft_note_only_while_a_better_voice_waits(job_with_plan, monkeypatch):
    write({})
    assert cli._draft_note(job_with_plan) == []
    paid(monkeypatch)
    assert cli._draft_note(job_with_plan) == ["Voix : brouillon gratuit, lance finale pour la voix ElevenLabs"]
    config.mark_final(job_with_plan)
    assert cli._draft_note(job_with_plan) == []
