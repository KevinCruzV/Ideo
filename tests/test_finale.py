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
    assert config.engine(job_with_plan) == "edge"


def test_kyutai_reste_possible_pour_le_brouillon_si_on_le_demande(job_with_plan, monkeypatch):
    write({"engine": "kyutai"})
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


def test_finale_keeps_the_voice_of_the_job_when_the_default_voice_changes(job_with_plan, monkeypatch):
    paid(monkeypatch)
    write({"engine": "elevenlabs", "elevenlabs_voice_id": "george", "elevenlabs_stability": 0.3})
    config.mark_final(job_with_plan)
    plan = common.load_json(job_with_plan / "plan.json")
    part = plan["parts"][0]
    before = pipeline.part_hash(plan, part, job_with_plan)
    write({"engine": "elevenlabs", "elevenlabs_voice_id": "jessica", "elevenlabs_stability": 0.45})
    assert config.eleven_voice_id(job_with_plan) == "george"
    assert config.eleven_settings(job_with_plan)["stability"] == 0.3
    assert config.eleven_voice_id() == "jessica"
    assert pipeline.part_hash(plan, part, job_with_plan) == before
    log = job_with_plan / "logs" / "v.log"
    assert voice.choose_backend("fr", log, job_with_plan).voice == "george"


def test_an_old_final_job_locks_its_voice_at_the_next_produce(job_with_plan, monkeypatch):
    paid(monkeypatch)
    (job_with_plan / config.FINAL_FILE).write_text('{"engine": "elevenlabs"}\n', encoding="utf-8")
    write({"engine": "elevenlabs", "elevenlabs_voice_id": "george"})
    config.lock_final_voice(job_with_plan)
    write({"engine": "elevenlabs", "elevenlabs_voice_id": "jessica"})
    assert config.eleven_voice_id(job_with_plan) == "george"


def test_a_big_paid_redo_waits_for_payer(job_with_plan, monkeypatch):
    paid(monkeypatch)
    config.mark_final(job_with_plan)
    pending = [("seg_01", "mot " * 200)]
    voice.paid_guard(job_with_plan, 1, pending, "fr", False)
    config.add_paid_characters(job_with_plan, 4000)
    try:
        voice.paid_guard(job_with_plan, 1, pending, "fr", False)
    except common.IdeoError as err:
        assert "--payer" in str(err) and "caractères ElevenLabs" in str(err)
    else:
        raise AssertionError("la dépense aurait dû être bloquée")
    voice.paid_guard(job_with_plan, 1, pending, "fr", True)
    voice.paid_guard(job_with_plan, 1, [("seg_01", "Une phrase corrigée.")], "fr", False)


def test_cli_produce_accepts_payer():
    assert cli.parse(["produce", "job", "--payer"])[3].get("payer") is True
