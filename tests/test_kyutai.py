import json
import wave
from pathlib import Path

import pytest

from ideo import common, config, voice
from tests.conftest import write_sine_wav


@pytest.fixture
def kyutai(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "kyutai_available", lambda: True)
    monkeypatch.setattr(config, "kyutai_installed", lambda: True)
    monkeypatch.setattr(config, "apple_silicon", lambda: True)
    py = tmp_path / "py"
    py.write_text("", encoding="utf-8")
    monkeypatch.setattr(config, "KYUTAI_PYTHON", py)
    calls = []
    real_run = common.run

    def fake_run(cmd, log):
        if str(cmd[0]) != str(py):
            return real_run(cmd, log)
        jsonl = Path(cmd[cmd.index("run_tts") + 1]) if "run_tts" in cmd else Path(cmd[3])
        out = Path(cmd[cmd.index("--out-folder") + 1])
        requests = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines()]
        calls.append({"cmd": [str(c) for c in cmd], "requests": requests})
        if getattr(fake_run, "fail", None):
            raise common.IdeoError(fake_run.fail)
        out.mkdir(parents=True, exist_ok=True)
        for request in requests:
            if request["id"] in getattr(fake_run, "skip", ()):
                continue
            write_sine_wav(out / f"{request['id']}.wav", seconds=0.8, rate=24000)

    monkeypatch.setattr(common, "run", fake_run)
    fake_run.calls = calls
    fake_run.pitch = {}
    taken = {}

    def fake_score(wav):
        name = Path(wav).stem
        taken[name] = taken.get(name, 0) + 1
        values = fake_run.pitch.get(name, [3.0])
        return values[min(taken[name] - 1, len(values) - 1)]

    monkeypatch.setattr(voice.prosody, "score", fake_score)
    return fake_run


def script_words(job, n=1):
    plan = common.load_json(job / "plan.json")
    return {name: text for name, text in voice.segments(plan, plan["parts"][0])}


def faithful(monkeypatch, scores=None):
    texts = {}
    seen = {"count": {}}

    def fake(wav, lang, log=None):
        name = Path(wav).stem
        seen["count"][name] = seen["count"].get(name, 0) + 1
        text = texts[name]
        words = text.split()
        quality = (scores or {}).get(name, [1.0])
        keep = quality[min(seen["count"][name] - 1, len(quality) - 1)]
        words = words[:max(1, round(len(words) * keep))]
        return [{"w": w, "s": i * 0.1, "e": i * 0.1 + 0.08} for i, w in enumerate(words)]

    monkeypatch.setattr(voice, "retranscribe", fake)
    return texts, seen


def test_the_whole_part_is_synthesised_in_one_subprocess(kyutai, job_with_plan, monkeypatch):
    texts, _ = faithful(monkeypatch)
    texts.update(script_words(job_with_plan))
    backend = voice.KyutaiBackend(job_with_plan / "logs" / "voice-01.log")
    voice.voice_part(job_with_plan, 1, backend=backend)
    assert len(kyutai.calls) == 1
    call = kyutai.calls[0]
    assert [r["id"] for r in call["requests"]] == list(texts)
    assert all(r["voices"] == ["unmute-prod-website/developpeuse-3.wav"] and r["turns"] == [texts[r["id"]]]
               for r in call["requests"])
    assert "--only-wav" in call["cmd"] and call["cmd"][call["cmd"].index("--padding-bonus") + 1] == "0.5"


def test_wavs_are_48k_mono_and_words_match_the_script(kyutai, job_with_plan, monkeypatch):
    texts, _ = faithful(monkeypatch)
    texts.update(script_words(job_with_plan))
    voice.voice_part(job_with_plan, 1, backend=voice.KyutaiBackend(job_with_plan / "logs" / "v.log"))
    part = job_with_plan / "parts" / "01"
    with wave.open(str(part / "seg_01.wav"), "rb") as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (48000, 1, 2)
    words = common.load_json(part / "seg_01.words.json")
    assert [w["w"] for w in words] == texts["seg_01"].split()


def test_config_voice_and_padding_are_passed(kyutai, job_with_plan, monkeypatch):
    texts, _ = faithful(monkeypatch)
    texts.update(script_words(job_with_plan))
    (common._root() / "config.json").write_text(json.dumps({"kyutai_voice": "x/y.wav", "kyutai_padding_bonus": -1}),
                                                encoding="utf-8")
    voice.voice_part(job_with_plan, 1, backend=voice.KyutaiBackend(job_with_plan / "logs" / "v.log"))
    call = kyutai.calls[0]
    assert call["requests"][0]["voices"] == ["x/y.wav"] and call["cmd"][call["cmd"].index("--padding-bonus") + 1] == "-1"


def test_unfaithful_segment_is_redone_and_the_best_is_kept(kyutai, job_with_plan, monkeypatch):
    texts, seen = faithful(monkeypatch, {"seg_02": [0.5, 0.7, 0.95]})
    texts.update(script_words(job_with_plan))
    voice.voice_part(job_with_plan, 1, backend=voice.KyutaiBackend(job_with_plan / "logs" / "v.log"))
    assert seen["count"]["seg_02"] == 3 and seen["count"]["seg_01"] == 1
    assert [r["id"] for r in kyutai.calls[1]["requests"]] == ["seg_02"] and len(kyutai.calls) == 3
    quality = common.load_json(job_with_plan / "parts" / "01" / "voice-quality.json")
    assert quality["seg_02"] >= 0.9 and quality["seg_01"] == 1.0
    log = (job_with_plan / "logs" / "voice-01.log").read_text(encoding="utf-8")
    assert "segments refaits : 2" in log


def test_at_most_three_redos_and_the_best_attempt_wins(kyutai, job_with_plan, monkeypatch):
    texts, seen = faithful(monkeypatch, {"seg_03": [0.4, 0.5, 0.3, 0.2]})
    texts.update(script_words(job_with_plan))
    voice.voice_part(job_with_plan, 1, backend=voice.KyutaiBackend(job_with_plan / "logs" / "v.log"))
    assert seen["count"]["seg_03"] == 4 and len(kyutai.calls) == 4
    quality = common.load_json(job_with_plan / "parts" / "01" / "voice-quality.json")
    assert 0.6 <= quality["seg_03"] < 0.9
    assert "segments refaits : 3" in (job_with_plan / "logs" / "voice-01.log").read_text(encoding="utf-8")


def test_existing_segments_are_not_redone(kyutai, job_with_plan, monkeypatch):
    texts, _ = faithful(monkeypatch)
    texts.update(script_words(job_with_plan))
    backend = voice.KyutaiBackend(job_with_plan / "logs" / "v.log")
    voice.voice_part(job_with_plan, 1, backend=backend)
    voice.voice_part(job_with_plan, 1, backend=backend)
    assert len(kyutai.calls) == 1


def test_engine_failure_falls_back_to_edge_and_says_so(kyutai, job_with_plan, monkeypatch, fake_backend, fake_whisper):
    kyutai.fail = "La commande a échoué (code 1) : moshi"
    monkeypatch.setattr(voice, "get_backend", lambda log=None: fake_backend)
    paths = voice.voice_part(job_with_plan, 1)
    assert len(paths) == 7 and len(fake_backend.calls) == 7
    info = common.load_json(job_with_plan / "parts" / "01" / "voice-info.json")
    assert info["engine"] == "edge" and "La commande a échoué" in info["fallback"] and "\n" not in info["fallback"]


def test_missing_output_file_falls_back(kyutai, job_with_plan, monkeypatch, fake_backend, fake_whisper):
    kyutai.skip = ("seg_02",)
    monkeypatch.setattr(voice, "get_backend", lambda log=None: fake_backend)
    voice.voice_part(job_with_plan, 1)
    assert common.load_json(job_with_plan / "parts" / "01" / "voice-info.json")["fallback"]


def test_other_languages_use_edge(kyutai, job_with_plan, monkeypatch, fake_backend, fake_whisper):
    plan = common.load_json(job_with_plan / "plan.json")
    plan["lang"] = "de"
    common.save_json(job_with_plan / "plan.json", plan)
    monkeypatch.setattr(voice, "get_backend", lambda log=None: fake_backend)
    voice.voice_part(job_with_plan, 1)
    assert kyutai.calls == []
    assert common.load_json(job_with_plan / "parts" / "01" / "voice-info.json") == {"engine": "edge", "fallback": None, "local_missing": False}


def test_kyutai_serves_french_and_english(kyutai, job_with_plan, monkeypatch):
    assert isinstance(voice.choose_backend("fr", job_with_plan / "l.log"), voice.KyutaiBackend)
    assert isinstance(voice.choose_backend("en", job_with_plan / "l.log"), voice.KyutaiBackend)
    assert isinstance(voice.choose_backend("es", job_with_plan / "l.log"), voice.EdgeTTSBackend)
    (common._root() / "config.json").write_text('{"engine": "edge"}', encoding="utf-8")
    assert isinstance(voice.choose_backend("fr", job_with_plan / "l.log"), voice.EdgeTTSBackend)


def test_missing_environment_is_a_clear_error(job_with_plan, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "KYUTAI_PYTHON", tmp_path / "absent")
    with pytest.raises(common.IdeoError, match="moteur de voix local"):
        voice.KyutaiBackend(job_with_plan / "logs" / "v.log").synthesize_batch([("a", "Bonjour")], "fr", tmp_path)


def test_hash_follows_engine_voice_and_padding(kyutai, job_with_plan):
    from ideo import pipeline

    plan = common.load_json(job_with_plan / "plan.json")
    part = plan["parts"][0]
    base = pipeline.part_hash(plan, part)
    cfg = common._root() / "config.json"
    cfg.write_text('{"engine": "edge"}', encoding="utf-8")
    assert pipeline.part_hash(plan, part) != base
    cfg.write_text('{"kyutai_padding_bonus": 1}', encoding="utf-8")
    assert pipeline.part_hash(plan, part) != base
    cfg.write_text('{"kyutai_voice": "a/b.wav"}', encoding="utf-8")
    assert pipeline.part_hash(plan, part) != base
    cfg.write_text('{}', encoding="utf-8")
    assert pipeline.part_hash(plan, part) == base


def test_missing_local_voice_is_recorded_for_the_online_voice(job_with_plan, monkeypatch, fake_backend, fake_whisper):
    monkeypatch.setattr(config, "apple_silicon", lambda: True)
    monkeypatch.setattr(voice, "get_backend", lambda log=None: fake_backend)
    voice.voice_part(job_with_plan, 1)
    info = common.load_json(job_with_plan / "parts" / "01" / "voice-info.json")
    assert info == {"engine": "edge", "fallback": None, "local_missing": True}
    assert len(fake_backend.calls) == 7


def test_all_segments_to_redo_share_one_call_per_pass(kyutai, job_with_plan, monkeypatch):
    texts, seen = faithful(monkeypatch, {"seg_01": [0.4, 0.95], "seg_03": [0.4, 0.5, 0.95], "seg_04": [0.4, 0.95]})
    texts.update(script_words(job_with_plan))
    voice.voice_part(job_with_plan, 1, backend=voice.KyutaiBackend(job_with_plan / "logs" / "v.log"))
    ids = [[r["id"] for r in call["requests"]] for call in kyutai.calls]
    assert len(ids) == 3 and len(ids[0]) == 7
    assert ids[1] == ["seg_01", "seg_03", "seg_04"] and ids[2] == ["seg_03"]


def run_part(kyutai, job, monkeypatch, scores=None, pitch=None):
    texts, seen = faithful(monkeypatch, scores)
    texts.update(script_words(job))
    kyutai.pitch.update(pitch or {})
    voice.voice_part(job, 1, backend=voice.KyutaiBackend(job / "logs" / "v.log"))
    return [[r["id"] for r in c["requests"]] for c in kyutai.calls], seen


def test_flat_segment_is_redone_with_a_higher_temperature(kyutai, job_with_plan, monkeypatch):
    ids, _ = run_part(kyutai, job_with_plan, monkeypatch, pitch={"seg_02": [1.5, 2.6]})
    assert len(ids) == 2 and ids[1] == ["seg_02"]
    assert "--temp" not in kyutai.calls[0]["cmd"]
    assert kyutai.calls[1]["cmd"][kyutai.calls[1]["cmd"].index("--temp") + 1] == "0.75"
    assert common.load_json(job_with_plan / "parts" / "01" / "voice-prosody.json")["seg_02"] == 2.6


def test_temperature_rises_pass_after_pass(kyutai, job_with_plan, monkeypatch):
    run_part(kyutai, job_with_plan, monkeypatch, pitch={"seg_02": [1.0, 1.1, 1.2, 1.3]})
    temps = [c["cmd"][c["cmd"].index("--temp") + 1] for c in kyutai.calls[1:]]
    assert temps == ["0.75", "0.9", "1"]


def test_hook_and_outro_need_2_4(kyutai, job_with_plan, monkeypatch):
    ids, _ = run_part(kyutai, job_with_plan, monkeypatch, pitch={"seg_00_hook": [2.2, 2.5], "seg_99_outro": [2.3, 2.45], "seg_01": [2.2]})
    assert len(ids) == 2 and sorted(ids[1]) == ["seg_00_hook", "seg_99_outro"]


def test_lively_enough_segment_is_not_redone(kyutai, job_with_plan, monkeypatch):
    ids, _ = run_part(kyutai, job_with_plan, monkeypatch, pitch={"seg_02": [2.0], "seg_00_hook": [2.4]})
    assert len(ids) == 1


def test_unscored_segment_is_not_considered_flat(kyutai, job_with_plan, monkeypatch):
    ids, _ = run_part(kyutai, job_with_plan, monkeypatch, pitch={"seg_02": [None]})
    assert len(ids) == 1


def test_flat_and_unfaithful_share_the_same_grouped_pass(kyutai, job_with_plan, monkeypatch):
    ids, _ = run_part(kyutai, job_with_plan, monkeypatch, scores={"seg_01": [0.4, 1.0]}, pitch={"seg_03": [1.0, 2.5]})
    assert len(ids) == 2 and sorted(ids[1]) == ["seg_01", "seg_03"]


def test_among_faithful_takes_the_liveliest_wins(kyutai, job_with_plan, monkeypatch):
    ids, _ = run_part(kyutai, job_with_plan, monkeypatch, pitch={"seg_02": [1.2, 1.9, 1.5, 1.4]})
    assert len(ids) == 4
    assert common.load_json(job_with_plan / "parts" / "01" / "voice-prosody.json")["seg_02"] == 1.9


def test_an_unfaithful_take_never_beats_a_faithful_one(kyutai, job_with_plan, monkeypatch):
    run_part(kyutai, job_with_plan, monkeypatch, scores={"seg_02": [1.0, 0.4, 0.4, 0.4]}, pitch={"seg_02": [1.2, 3.5, 3.5, 3.5]})
    assert common.load_json(job_with_plan / "parts" / "01" / "voice-prosody.json")["seg_02"] == 1.2
    assert common.load_json(job_with_plan / "parts" / "01" / "voice-quality.json")["seg_02"] == 1.0


def test_best_take_helpers():
    take = lambda f, p: {"fidelity": f, "prosody": p}
    assert voice.best_take([take(0.95, 1.0), take(0.92, 2.5), take(0.5, 4.0)]) == take(0.92, 2.5)
    assert voice.best_take([take(0.5, 4.0), take(0.7, 1.0)]) == take(0.7, 1.0)
    assert voice.needs_redo("seg_01", take(0.95, 1.9)) and not voice.needs_redo("seg_01", take(0.95, 2.0))
    assert voice.needs_redo("seg_99_outro", take(0.95, 2.39)) and not voice.needs_redo("seg_99_outro", take(0.95, 2.4))
    assert not voice.needs_redo("seg_01", take(0.95, None)) and voice.needs_redo("seg_01", take(0.5, 3.0))


def test_log_reports_the_median_intonation(kyutai, job_with_plan, monkeypatch):
    run_part(kyutai, job_with_plan, monkeypatch)
    assert "intonation médiane : 3.0" in (job_with_plan / "logs" / "voice-01.log").read_text(encoding="utf-8")


def test_lexicon_respells_only_the_text_sent_to_the_engine(kyutai, job_with_plan, monkeypatch):
    path = common._root() / "skills" / "ideo" / "references" / "prononciation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"fr": {"face": "fasse", "mémoire": "mémoire"}}', encoding="utf-8")
    plan = common.load_json(job_with_plan / "plan.json")
    plan["parts"][0]["hook"] = "Face à face, tu oublies ?"
    common.save_json(job_with_plan / "plan.json", plan)
    texts, _ = faithful(monkeypatch)
    spoken_texts = {}

    def fake_heard(wav, lang, log=None):
        name = Path(wav).stem
        return [{"w": w, "s": i * 0.1, "e": i * 0.1 + 0.08} for i, w in enumerate(spoken_texts[name].split())]

    monkeypatch.setattr(voice, "retranscribe", fake_heard)
    spoken_texts.update(script_words(job_with_plan))
    spoken_texts["seg_00_hook"] = "Fasse à fasse, tu oublies ?"
    voice.voice_part(job_with_plan, 1, backend=voice.KyutaiBackend(job_with_plan / "logs" / "v.log"))
    sent = kyutai.calls[0]["requests"][0]["turns"][0]
    assert sent == "Fasse à fasse, tu oublies ?"
    words = common.load_json(job_with_plan / "parts" / "01" / "seg_00_hook.words.json")
    assert [w["w"] for w in words] == ["Face", "à", "face,", "tu", "oublies?"]
    assert words[0]["e"] > words[0]["s"] and words[2]["s"] > words[1]["s"]
    quality = common.load_json(job_with_plan / "parts" / "01" / "voice-quality.json")
    assert quality["seg_00_hook"] == 1.0


def test_changing_the_lexicon_redoes_only_the_affected_segments(kyutai, job_with_plan, monkeypatch):
    plan = common.load_json(job_with_plan / "plan.json")
    plan["parts"][0]["hook"] = "Face à face, tu oublies ?"
    common.save_json(job_with_plan / "plan.json", plan)
    texts, seen = faithful(monkeypatch)
    texts.update(script_words(job_with_plan))
    texts["seg_00_hook"] = "Face à face, tu oublies ?"

    def heard(wav, lang, log=None):
        name = Path(wav).stem
        return [{"w": w, "s": i * 0.1, "e": i * 0.1 + 0.08} for i, w in enumerate(
            (lexicon_text(name)).split())]

    from ideo import lexicon

    def lexicon_text(name):
        return lexicon.apply(texts[name], "fr")

    monkeypatch.setattr(voice, "retranscribe", heard)
    backend = voice.KyutaiBackend(job_with_plan / "logs" / "v.log")
    voice.voice_part(job_with_plan, 1, backend=backend)
    assert len(kyutai.calls) == 1
    lexicon.add("face", "fasse")
    voice.voice_part(job_with_plan, 1, backend=backend)
    assert len(kyutai.calls) == 2 and [r["id"] for r in kyutai.calls[1]["requests"]] == ["seg_00_hook"]
    voice.voice_part(job_with_plan, 1, backend=backend)
    assert len(kyutai.calls) == 2
