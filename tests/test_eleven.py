import base64
import json
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ideo import cli, common, config, eleven, voice
from tests.conftest import write_sine_wav
from tests.test_cli import produce_job

KEY = "sk_test_cle_secrete_123456"


class Server:
    def __init__(self):
        self.requests = []
        self.fail = None
        self.voices = [{"voice_id": "v1", "name": "Rachel", "labels": {"accent": "american", "gender": "female", "language": "en"}},
                       {"voice_id": "v2", "name": "Antoine", "labels": {"accent": "français"}}]
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, status, body, headers=None):
                data = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                for k, v in (headers or {}).items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                owner.requests.append({"method": "POST", "path": self.path, "headers": dict(self.headers.items()), "body": body})
                if owner.fail:
                    status, payload = owner.fail
                    return self._send(status, {"detail": payload})
                text = body["text"]
                import tempfile

                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "a.wav"
                    write_sine_wav(path, seconds=max(0.5, len(text) * 0.04), rate=24000)
                    audio = base64.b64encode(path.read_bytes()).decode()
                chars = list(text)
                starts = [round(i * 0.04, 3) for i in range(len(chars))]
                ends = [round(i * 0.04 + 0.04, 3) for i in range(len(chars))]
                self._send(200, {"audio_base64": audio, "alignment": {"characters": chars, "character_start_times_seconds": starts,
                                                                       "character_end_times_seconds": ends}},
                           {"request-id": f"req{len(owner.requests)}"})

            def do_GET(self):
                owner.requests.append({"method": "GET", "path": self.path, "headers": dict(self.headers.items())})
                if owner.fail:
                    status, payload = owner.fail
                    return self._send(status, {"detail": payload})
                self._send(200, {"voices": owner.voices, "has_more": False})

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


@pytest.fixture
def server(monkeypatch):
    srv = Server()
    monkeypatch.setattr(eleven, "API_BASE", srv.url)
    monkeypatch.setenv("ELEVENLABS_API_KEY", KEY)
    yield srv
    srv.close()


def header(request, name):
    return next(v for k, v in request["headers"].items() if k.lower() == name.lower())


def configure(settings):
    (common._root() / "config.json").write_text(json.dumps({"engine": "elevenlabs", "elevenlabs_voice_id": "voix123", **settings}),
                                                encoding="utf-8")


def drop_question(job):
    plan = common.load_json(job / "plan.json")
    for part in plan["parts"]:
        part.pop("question", None)
    common.save_json(job / "plan.json", plan)


@pytest.fixture
def eleven_job(job_with_plan, server, monkeypatch):
    configure({})
    config.mark_final(job_with_plan)
    drop_question(job_with_plan)
    monkeypatch.setattr(voice, "retranscribe", lambda wav, lang, log=None: [])
    monkeypatch.setattr(voice.fidelity, "similarity", lambda a, b: 1.0)
    return job_with_plan


def test_request_uses_the_documented_endpoint_headers_and_parameters(server, tmp_path):
    configure({"elevenlabs_model": "eleven_turbo_v2_5", "elevenlabs_stability": 0.7, "elevenlabs_speed": 0.95})
    backend = eleven.ElevenLabsBackend(tmp_path / "l.log")
    backend.synthesize("Bonjour tout le monde.", "fr", tmp_path / "a.wav", previous_text="Avant.", next_text="Après.")
    request = server.requests[0]
    assert request["path"] == "/v1/text-to-speech/voix123/with-timestamps"
    assert header(request, "xi-api-key") == KEY and header(request, "Content-Type") == "application/json"
    body = request["body"]
    assert body["text"] == "Bonjour tout le monde." and body["model_id"] == "eleven_turbo_v2_5"
    assert body["voice_settings"] == {"stability": 0.7, "similarity_boost": 0.8, "style": 0.3, "speed": 0.95, "use_speaker_boost": True}
    assert body["previous_text"] == "Avant." and body["next_text"] == "Après." and "previous_request_ids" not in body


def test_defaults_are_a_calm_narration(server, tmp_path):
    configure({})
    eleven.ElevenLabsBackend().synthesize("Salut.", "fr", tmp_path / "a.wav")
    body = server.requests[0]["body"]
    assert body["model_id"] == "eleven_multilingual_v2"
    assert body["voice_settings"]["stability"] == 0.45 and body["voice_settings"]["style"] == 0.3 and body["voice_settings"]["speed"] == 1.0


def test_continuity_uses_previous_request_ids_then_drops_previous_text(server, tmp_path):
    configure({})
    backend = eleven.ElevenLabsBackend()
    for i in range(5):
        backend.synthesize(f"Phrase {i}.", "fr", tmp_path / f"{i}.wav", previous_text="Avant", next_text="Suite")
    bodies = [r["body"] for r in server.requests]
    assert "previous_text" in bodies[0] and "previous_request_ids" not in bodies[0]
    assert bodies[1]["previous_request_ids"] == ["req1"] and "previous_text" not in bodies[1]
    assert bodies[4]["previous_request_ids"] == ["req2", "req3", "req4"]
    assert all(b["next_text"] == "Suite" for b in bodies)


def test_word_timings_come_from_the_character_alignment(server, tmp_path):
    configure({})
    words = eleven.ElevenLabsBackend().synthesize("Un deux trois.", "fr", tmp_path / "a.wav")
    assert [w["w"] for w in words] == ["Un", "deux", "trois."]
    assert words[0]["s"] == 0.0 and words[0]["e"] == 0.08 and words[1]["s"] == 0.12 and words[2]["e"] == pytest.approx(0.56)


def test_alignment_helper_edge_cases():
    assert eleven.words_from_alignment(None) is None
    assert eleven.words_from_alignment({"characters": ["a"], "character_start_times_seconds": [], "character_end_times_seconds": []}) is None
    assert eleven.words_from_alignment({"characters": [" ", " "], "character_start_times_seconds": [0, 1],
                                        "character_end_times_seconds": [1, 2]}) is None


def test_audio_is_converted_to_48k_mono(server, tmp_path):
    configure({})
    eleven.ElevenLabsBackend().synthesize("Bonjour.", "fr", tmp_path / "a.wav")
    with wave.open(str(tmp_path / "a.wav"), "rb") as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (48000, 1, 2)


def test_characters_are_counted(server, tmp_path):
    configure({})
    backend = eleven.ElevenLabsBackend()
    backend.synthesize("Bonjour.", "fr", tmp_path / "a.wav")
    backend.synthesize("Au revoir.", "fr", tmp_path / "b.wav")
    assert backend.characters == len("Bonjour.") + len("Au revoir.")


def test_default_voice_is_used_when_none_is_chosen(server):
    (common._root() / "config.json").write_text('{"engine": "elevenlabs"}', encoding="utf-8")
    assert eleven.ElevenLabsBackend().voice == "cgSgspJ2msm6clMCkdW9"


def test_missing_key_is_a_clear_error(monkeypatch, tmp_path):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    configure({})
    with pytest.raises(common.IdeoError, match="ELEVENLABS_API_KEY"):
        eleven.ElevenLabsBackend().synthesize("x", "fr", tmp_path / "a.wav")


def test_key_can_come_from_config_and_the_environment_wins(monkeypatch, server, tmp_path):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    configure({"elevenlabs_api_key": "cle_du_fichier"})
    eleven.ElevenLabsBackend().synthesize("x", "fr", tmp_path / "a.wav")
    assert header(server.requests[-1], "xi-api-key") == "cle_du_fichier"
    monkeypatch.setenv("ELEVENLABS_API_KEY", KEY)
    eleven.ElevenLabsBackend().synthesize("x", "fr", tmp_path / "a.wav")
    assert header(server.requests[-1], "xi-api-key") == KEY


def test_key_can_come_from_dotenv_between_environment_and_config(monkeypatch, server, tmp_path):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    configure({"elevenlabs_api_key": "cle_du_fichier"})
    (common._root() / ".env").write_text("ELEVENLABS_API_KEY=cle_du_dotenv\n", encoding="utf-8")
    try:
        eleven.ElevenLabsBackend().synthesize("x", "fr", tmp_path / "a.wav")
        assert header(server.requests[-1], "xi-api-key") == "cle_du_dotenv"
        monkeypatch.setenv("ELEVENLABS_API_KEY", KEY)
        eleven.ElevenLabsBackend().synthesize("x", "fr", tmp_path / "a.wav")
        assert header(server.requests[-1], "xi-api-key") == KEY
    finally:
        (common._root() / ".env").unlink()


@pytest.mark.parametrize("status,fragment", [(401, "refusée"), (402, "quota"), (429, "quota"), (404, "introuvable"), (500, "500")])
def test_http_errors_are_french_and_never_contain_the_key(server, tmp_path, status, fragment):
    configure({})
    server.fail = (status, f"echec avec {KEY} dans le corps")
    with pytest.raises(common.IdeoError) as err:
        eleven.ElevenLabsBackend().synthesize("x", "fr", tmp_path / "a.wav")
    assert fragment in str(err.value) and KEY not in str(err.value)


def test_network_error_is_french(monkeypatch, tmp_path):
    monkeypatch.setattr(eleven, "API_BASE", "http://127.0.0.1:9")
    monkeypatch.setenv("ELEVENLABS_API_KEY", KEY)
    configure({})
    with pytest.raises(common.IdeoError, match="connexion à ElevenLabs impossible") as err:
        eleven.ElevenLabsBackend().synthesize("x", "fr", tmp_path / "a.wav")
    assert KEY not in str(err.value)


def test_mask_hides_the_key_and_header_values():
    assert KEY not in eleven._mask(f"erreur {KEY} et xi-api-key: {KEY}", KEY)
    assert "***" in eleven._mask("xi-api-key: abc123", None)


def tree_text(root):
    out = []
    for path in Path(root).rglob("*"):
        if path.is_file() and path.suffix in (".json", ".log", ".txt", ".md"):
            out.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(out)


def test_voice_part_with_elevenlabs_writes_script_words_and_costs(eleven_job, server):
    job = eleven_job
    paths = voice.voice_part(job, 1)
    assert len(paths) == 7 and len(server.requests) == 7
    info = common.load_json(job / "parts" / "01" / "voice-info.json")
    plan = common.load_json(job / "plan.json")
    total = sum(len(t) for _, t in voice.segments(plan, plan["parts"][0]))
    assert info["engine"] == "elevenlabs" and info["fallback"] is None and info["characters"] == total
    words = common.load_json(job / "parts" / "01" / "seg_01.words.json")
    assert [w["w"] for w in words] == voice.align.script_words(plan["parts"][0]["scenes"][0]["say"])
    assert f"{total} caractères" in (job / "logs" / "voice-01.log").read_text(encoding="utf-8")


def test_the_key_never_reaches_a_file_of_the_job(eleven_job, server):
    voice.voice_part(eleven_job, 1)
    assert KEY not in tree_text(eleven_job)
    server.fail = (401, f"clé {KEY} refusée")
    import shutil

    shutil.rmtree(eleven_job / "parts")
    voice.voice_part(eleven_job, 1, backend=eleven.ElevenLabsBackend(eleven_job / "logs" / "x.log"))
    assert KEY not in tree_text(eleven_job)


def test_numbers_are_sent_as_digits_and_the_lexicon_still_applies(eleven_job, server):
    plan = common.load_json(eleven_job / "plan.json")
    plan["parts"][0]["scenes"][0]["say"] = "En 1998, la face cachée coûte 3 000 euros."
    common.save_json(eleven_job / "plan.json", plan)
    path = common._root() / "skills" / "ideo" / "references" / "prononciation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"fr": {"face": "fasse"}}', encoding="utf-8")
    voice.voice_part(eleven_job, 1)
    sent = [r["body"]["text"] for r in server.requests]
    assert "En 1998, la fasse cachée coûte 3 000 euros." in sent
    words = common.load_json(eleven_job / "parts" / "01" / "seg_01.words.json")
    assert [w["w"] for w in words][:3] == ["En", "1998,", "la"] and "face" in [w["w"] for w in words]


def test_continuity_between_segments_in_a_part(eleven_job, server):
    voice.voice_part(eleven_job, 1)
    bodies = [r["body"] for r in server.requests]
    assert "previous_text" not in bodies[0] and "next_text" in bodies[0]
    assert bodies[1]["previous_request_ids"] == ["req1"]
    assert "next_text" not in bodies[-1] and bodies[-1]["previous_request_ids"]


def test_at_most_one_retry_and_only_under_080(eleven_job, server, monkeypatch):
    plan = common.load_json(eleven_job / "plan.json")
    texts = dict(voice.segments(plan, plan["parts"][0]))
    calls = {}

    def fake(wav, lang, log=None):
        name = Path(wav).name
        calls[name] = calls.get(name, 0) + 1
        return []

    monkeypatch.setattr(voice, "retranscribe", fake)
    voice.voice_part(eleven_job, 1)
    assert len(server.requests) == 7
    server.requests.clear()
    import shutil

    shutil.rmtree(eleven_job / "parts")
    scores = iter([0.3, 0.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

    monkeypatch.setattr(voice.fidelity, "similarity", lambda a, b: next(scores))
    voice.voice_part(eleven_job, 1)
    assert len(server.requests) == 8
    quality = common.load_json(eleven_job / "parts" / "01" / "voice-quality.json")
    assert quality["seg_00_hook"] == 0.3
    info = common.load_json(eleven_job / "parts" / "01" / "voice-info.json")
    assert info["characters"] == sum(len(t) for t in texts.values()) + len(texts["seg_00_hook"])


def test_an_added_word_triggers_one_retry_and_is_flagged_when_it_stays(eleven_job, server, monkeypatch):
    plan = common.load_json(eleven_job / "plan.json")
    texts = dict(voice.segments(plan, plan["parts"][0]))
    monkeypatch.setattr(voice, "retranscribe", lambda wav, lang, log=None: [{"w": texts[Path(wav).stem] + " tout", "s": 0.0, "e": 1.0}]
                        if Path(wav).stem == "seg_01" else [{"w": texts[Path(wav).stem], "s": 0.0, "e": 1.0}])
    voice.voice_part(eleven_job, 1)
    assert len(server.requests) == 8
    quality = common.load_json(eleven_job / "parts" / "01" / "voice-quality.json")
    assert quality["seg_01"] == eleven.ADDED_WORD_SCORE < 0.80
    assert quality["seg_02"] > 0.9
    log = (eleven_job / "logs" / "voice-01.log").read_text(encoding="utf-8")
    assert "garde un mot ajouté : tout" in log


def test_failure_falls_back_to_the_online_voice_and_says_so(eleven_job, server, monkeypatch, fake_backend):
    server.fail = (429, "quota")
    monkeypatch.setattr(voice, "get_backend", lambda log=None: fake_backend)
    voice.voice_part(eleven_job, 1)
    info = common.load_json(eleven_job / "parts" / "01" / "voice-info.json")
    assert info["engine"] == "edge" and "quota" in info["fallback"] and len(fake_backend.calls) == 7
    assert KEY not in tree_text(eleven_job)


def test_missing_key_falls_back_to_the_local_voice(eleven_job, monkeypatch, fake_backend):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setattr(voice, "get_backend", lambda log=None: fake_backend)
    voice.voice_part(eleven_job, 1)
    info = common.load_json(eleven_job / "parts" / "01" / "voice-info.json")
    assert info["engine"] == "edge" and "ELEVENLABS_API_KEY" in info["fallback"]


def test_failure_falls_back_to_kyutai_when_installed(eleven_job, server, monkeypatch):
    server.fail = (402, "quota")
    monkeypatch.setattr(config, "kyutai_installed", lambda: True)
    monkeypatch.setattr(config, "apple_silicon", lambda: True)
    made = {}

    class FakeLocal:
        local = True

        def __init__(self, log=None):
            made["used"] = True

    monkeypatch.setattr(voice, "KyutaiBackend", FakeLocal)
    monkeypatch.setattr(voice, "_settle_local", lambda backend, pending, lang, out_dir, log, key: (_ for _ in ()).throw(
        common.IdeoError("moteur local en panne")))
    with pytest.raises(common.IdeoError, match="moteur local en panne"):
        voice.voice_part(eleven_job, 1)
    assert made["used"] is True


def test_nothing_is_redone_when_the_text_has_not_changed(eleven_job, server):
    voice.voice_part(eleven_job, 1)
    server.requests.clear()
    voice.voice_part(eleven_job, 1)
    assert server.requests == []
    assert voice.stale(eleven_job, 1) == []


def test_changing_the_voice_changes_the_part_hash_but_not_the_key(eleven_job):
    from ideo import pipeline

    plan = common.load_json(eleven_job / "plan.json")
    part = plan["parts"][0]
    base = pipeline.part_hash(plan, part)
    configure({"elevenlabs_voice_id": "autre"})
    assert pipeline.part_hash(plan, part) != base
    configure({"elevenlabs_stability": 0.4})
    assert pipeline.part_hash(plan, part) != base
    configure({"elevenlabs_api_key": "autre_cle"})
    assert pipeline.part_hash(plan, part) == base


def test_voix_liste(server, capsys):
    assert cli.main(["voix-liste"]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out[0] == "OK voix-liste : 2 voix"
    assert out[1] == "Rachel | v1 | en, american, female" and out[2] == "Antoine | v2 | français"
    assert server.requests[0]["path"].startswith("/v2/voices?page_size=100")
    assert KEY not in "\n".join(out)


def test_voix_liste_without_a_key(monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert cli.main(["voix-liste"]) == 1
    out = capsys.readouterr().out.strip()
    assert out.startswith("ERREUR voix-liste : la clé ElevenLabs est absente (ELEVENLABS_API_KEY).") and "ELEVENLABS_API_KEY" in out


def test_voix_liste_paginates(server, capsys):
    pages = [{"voices": [{"voice_id": "a", "name": "A", "labels": {}}], "has_more": True, "next_page_token": "t2"},
             {"voices": [{"voice_id": "b", "name": "B", "labels": {}}], "has_more": False}]
    original = eleven._request

    def paged(method, path, key, body=None):
        return pages.pop(0), {}

    import ideo.eleven as module

    module._request = paged
    try:
        assert [v["id"] for v in eleven.list_voices()] == ["a", "b"]
    finally:
        module._request = original


def test_voix_test_reports_the_characters_consumed(server, capsys, home_dir=None):
    configure({})
    assert cli.main(["voix-test", "Bonjour,", "ceci", "est", "un", "essai."]) == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith(f"OK voix-test : {len('Bonjour, ceci est un essai.')} caractères consommés, durée ")
    assert out.endswith("voix-test.wav") and (common._root() / "voix-test.wav").exists()
    assert KEY not in out
    cli.main(["voix-test"])
    assert "caractères consommés" in capsys.readouterr().out


def test_voix_test_errors_are_one_line(monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    configure({})
    assert cli.main(["voix-test"]) == 1
    assert capsys.readouterr().out.startswith("ERREUR voix-test : la clé ElevenLabs est absente (ELEVENLABS_API_KEY).")


def test_config_validation_for_elevenlabs(home_dir=None):
    for bad in ({"elevenlabs_stability": 2}, {"elevenlabs_speed": 0.2}, {"elevenlabs_voice_id": ""}, {"elevenlabs_api_key": 3},
                {"elevenlabs_style": "x"}):
        (common._root() / "config.json").write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(common.IdeoError, match="config.json"):
            config.engine()
    (common._root() / "config.json").write_text('{"engine": "elevenlabs"}', encoding="utf-8")
    assert config.engine() == "elevenlabs"


def test_choose_backend_picks_elevenlabs(server, tmp_path):
    configure({})
    assert isinstance(voice.choose_backend("fr", tmp_path / "l.log"), eleven.ElevenLabsBackend)


def test_produce_line_carries_the_character_count(produce_job, server, monkeypatch, capsys):
    job = produce_job[0]
    configure({})
    config.mark_final(job)
    monkeypatch.setattr(voice, "retranscribe", lambda wav, lang, log=None: [])
    monkeypatch.setattr(voice.fidelity, "similarity", lambda a, b: 1.0)
    plan = common.load_json(job / "plan.json")
    total = sum(len(piece) for n, t in voice.segments(plan, plan["parts"][0]) for piece in voice._pieces(n, t))
    assert cli.main(["produce", str(job)]) == 0
    line = capsys.readouterr().out.strip().splitlines()[0]
    assert f" ; Voix : ElevenLabs, {total} caractères" in line and KEY not in line
    assert len(server.requests) == 8


def test_produce_line_says_the_fallback(produce_job, server, monkeypatch, capsys):
    job, backend, _ = produce_job
    configure({})
    config.mark_final(job)
    server.fail = (429, "quota")
    assert cli.main(["produce", str(job)]) == 0
    line = capsys.readouterr().out.strip().splitlines()[0]
    assert " ; Voix : repli sur la voix en ligne, quota ElevenLabs épuisé" in line


def test_voice_notes_for_elevenlabs_and_its_fallbacks(job_with_plan):
    job = job_with_plan
    parts = job / "parts"
    for n, info in ((1, {"engine": "elevenlabs", "fallback": None, "characters": 1200}),
                    (2, {"engine": "elevenlabs", "fallback": None, "characters": 300})):
        (parts / f"{n:02d}").mkdir(parents=True, exist_ok=True)
        common.save_json(parts / f"{n:02d}" / "voice-info.json", info)
    assert cli._voice_notes(job, None) == ["Voix : ElevenLabs, 1500 caractères"]
    assert cli._voice_notes(job, 2) == ["Voix : ElevenLabs, 300 caractères"]
    common.save_json(parts / "01" / "voice-info.json", {"engine": "kyutai", "fallback": "quota ElevenLabs épuisé"})
    assert "Voix : repli sur la voix locale, quota ElevenLabs épuisé" in cli._voice_notes(job, 1)
    common.save_json(parts / "01" / "voice-info.json", {"engine": "edge", "fallback": "quota ElevenLabs épuisé"})
    assert "Voix : repli sur la voix en ligne, quota ElevenLabs épuisé" in cli._voice_notes(job, 1)


def test_cost_and_check_estimate_the_characters(job_with_fixtures, server, capsys):
    from ideo import cost

    common.save_json(job_with_fixtures / "info.json", {"duration": 1800})
    for step in ("fetch", "transcribe", "transcript"):
        common.mark(job_with_fixtures, step, True)
    (job_with_fixtures / "transcript_compact.md").write_text("x", encoding="utf-8")
    (common._root() / "config.json").write_text('{"engine": "edge"}', encoding="utf-8")
    assert cost.eleven_note(job_with_fixtures) == ""
    configure({})
    note = cost.eleven_note(job_with_fixtures)
    assert note.startswith(" Voix ElevenLabs : environ 2 160 à 3 240 caractères") and "mots du say x 6" in note
    assert cli.main(["check", str(job_with_fixtures)]) == 0
    first = capsys.readouterr().out.strip().splitlines()[0]
    assert ", environ " in first and " caractères ElevenLabs" in first
    configure({"engine": "edge"})
    cli.main(["check", str(job_with_fixtures), "--sans-relecture"])
    assert "ElevenLabs" not in capsys.readouterr().out


def test_a_word_read_from_the_next_sentence_is_cut_off_the_end(eleven_job, server, monkeypatch):
    plan = common.load_json(eleven_job / "plan.json")
    texts = dict(voice.segments(plan, plan["parts"][0]))

    def listen(wav, lang, log=None):
        words = texts[Path(wav).stem].split()
        timed = [{"w": w, "s": i * 0.1, "e": i * 0.1 + 0.08} for i, w in enumerate(words)]
        if Path(wav).stem == "seg_01":
            timed.append({"w": "coup", "s": len(words) * 0.1 + 0.05, "e": len(words) * 0.1 + 0.3})
        return timed

    monkeypatch.setattr(voice, "retranscribe", listen)
    voice.voice_part(eleven_job, 1)
    quality = common.load_json(eleven_job / "parts" / "01" / "voice-quality.json")
    assert quality["seg_01"] > eleven.ADDED_WORD_SCORE
    log = (eleven_job / "logs" / "voice-01.log").read_text(encoding="utf-8")
    assert "coupe le mot ajouté en fin : coup" in log and "garde un mot ajouté" not in log
    with wave.open(str(eleven_job / "parts" / "01" / "seg_01.wav"), "rb") as w:
        length = w.getnframes() / w.getframerate()
    assert length < 0.7 * len(texts["seg_01"]) * 0.04


def test_a_paid_voice_drops_the_hook_and_pitch_files_left_by_the_local_voice(eleven_job, server):
    out_dir = eleven_job / "parts" / "01"
    out_dir.mkdir(parents=True, exist_ok=True)
    common.save_json(out_dir / "voice-hook.json", {"passed": False, "failed": ["fidelity"], "takes": 12})
    common.save_json(out_dir / "voice-prosody.json", {"seg_00_hook": 1.2, "seg_01": 1.4, "seg_99_outro": 1.9})
    voice.voice_part(eleven_job, 1)
    assert not (out_dir / "voice-hook.json").exists()
    assert not (out_dir / "voice-prosody.json").exists()


def test_the_final_question_is_voiced_on_its_own_then_the_subscribe_call(eleven_job, server):
    plan = common.load_json(eleven_job / "plan.json")
    plan["parts"][0]["question"] = "Pour toi, qui a gagné ?"
    common.save_json(eleven_job / "plan.json", plan)
    voice.voice_part(eleven_job, 1)
    bodies = [r["body"] for r in server.requests]
    assert len(bodies) == 8
    question, call = bodies[-2], bodies[-1]
    assert question["text"] == "Pour toi, qui a gagné ?" and question["next_text"] == call["text"]
    assert "?" not in call["text"] and call["previous_request_ids"]
    assert not (eleven_job / "parts" / "01" / "seg_99_outro.pieces").exists()
    words = common.load_json(eleven_job / "parts" / "01" / "seg_99_outro.words.json")
    full = voice.segments(common.load_json(eleven_job / "plan.json"), plan["parts"][0])[-1][1]
    assert [w["w"] for w in words] == voice.align.script_words(full)
    assert all(a["s"] <= b["s"] for a, b in zip(words, words[1:]))
