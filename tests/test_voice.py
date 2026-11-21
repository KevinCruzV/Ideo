import wave
from pathlib import Path

import pytest

from ideo import common, voice


def set_next_part(job):
    plan = common.load_json(job / "plan.json")
    plan["parts"].append({"n": 2, "title": "Le sommeil", "hook": "Et dormir ?", "scenes": []})
    common.save_json(job / "plan.json", plan)


def test_voice_part_creates_one_wav_per_segment(job_with_plan, fake_backend, fake_whisper):
    paths = voice.voice_part(job_with_plan, 1, backend=fake_backend)
    names = [p.name for p in paths]
    assert names == ["seg_00_hook.wav", "seg_01.wav", "seg_02.wav", "seg_03.wav", "seg_04.wav", "seg_05.wav",
                     "seg_99_outro.wav"]
    assert all(p.parent == job_with_plan / "parts" / "01" for p in paths)
    assert all(p.with_suffix(".words.json").exists() for p in paths)
    assert common.load_json(paths[0].with_suffix(".words.json")) == [{"w": "mot", "s": 0.0, "e": 0.3}]
    assert common.read_status(job_with_plan)["steps"]["voice-01"]["ok"] is True


def test_voice_part_texts_and_lang(job_with_plan, fake_backend, fake_whisper):
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    plan = common.load_json(job_with_plan / "plan.json")
    part = plan["parts"][0]
    assert fake_backend.calls[0][:2] == (part["hook"], "fr")
    assert fake_backend.calls[1][0] == part["scenes"][0]["say"]
    assert fake_backend.calls[-1][0] == "Abonne-toi pour la prochaine vidéo"
    assert all(lang == "fr" for _, lang in fake_whisper)


def test_voice_part_outro_next(job_with_plan, fake_backend, fake_whisper):
    set_next_part(job_with_plan)
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    assert fake_backend.calls[-1][0] == "Abonne-toi pour la partie 2 : Le sommeil"


def test_voice_part_outro_last_of_several_parts(job_with_plan, fake_backend, fake_whisper):
    set_next_part(job_with_plan)
    voice.voice_part(job_with_plan, 2, backend=fake_backend)
    assert fake_backend.calls[-1][0] == "Abonne-toi pour la prochaine série"


def test_voice_part_skips_existing_segments(job_with_plan, fake_backend, fake_whisper):
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    first = len(fake_backend.calls)
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    assert len(fake_backend.calls) == first == 7
    assert len(fake_whisper) == 7


def test_voice_part_regenerates_segment_missing_words(job_with_plan, fake_backend, fake_whisper):
    paths = voice.voice_part(job_with_plan, 1, backend=fake_backend)
    paths[2].with_suffix(".words.json").unlink()
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    assert len(fake_backend.calls) == 8


def test_voice_part_uses_plan_language(job_with_plan, fake_backend, fake_whisper):
    plan = common.load_json(job_with_plan / "plan.json")
    plan["lang"] = "de"
    common.save_json(job_with_plan / "plan.json", plan)
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    assert {c[1] for c in fake_backend.calls} == {"de"}
    assert fake_backend.calls[-1][0] == i18n_last("de")
    assert all(lang == "de" for _, lang in fake_whisper)


def i18n_last(lang):
    from ideo import i18n

    return i18n.t("outro_single", lang)


def test_voice_part_unknown_part(job_with_plan, fake_backend, fake_whisper):
    with pytest.raises(common.IdeoError, match="partie 9"):
        voice.voice_part(job_with_plan, 9, backend=fake_backend)


def test_voice_part_failure_marks_status(job_with_plan, fake_whisper):
    class Boom:
        def synthesize(self, text, lang, out_wav):
            raise common.IdeoError("réseau coupé")

    with pytest.raises(common.IdeoError, match="réseau"):
        voice.voice_part(job_with_plan, 1, backend=Boom())
    step = common.read_status(job_with_plan)["steps"]["voice-01"]
    assert step["ok"] is False and "réseau" in step["detail"]


def test_edge_backend_rejects_unknown_language():
    with pytest.raises(common.IdeoError, match="n'a pas de voix"):
        voice.EdgeTTSBackend().synthesize("x", "xx", Path("/tmp/x.wav"))


def test_edge_backend_voices():
    assert voice.EDGE_VOICES == {
        "fr": "fr-FR-HenriNeural", "en": "en-US-GuyNeural", "es": "es-ES-AlvaroNeural",
        "de": "de-DE-ChristophNeural", "it": "it-IT-DiegoNeural", "pt": "pt-BR-AntonioNeural",
        "nl": "nl-NL-MaartenNeural", "pl": "pl-PL-MarekNeural", "tr": "tr-TR-AhmetNeural",
        "ar": "ar-SA-HamedNeural", "ru": "ru-RU-DmitryNeural", "ja": "ja-JP-KeitaNeural",
        "ko": "ko-KR-InJoonNeural", "zh": "zh-CN-YunxiNeural", "hi": "hi-IN-MadhurNeural",
    }


def test_edge_backend_network_error_is_french(tmp_path, monkeypatch):
    import edge_tts

    class Failing:
        def __init__(self, text, voice):
            pass

        async def save(self, path):
            raise OSError("down")

    monkeypatch.setattr(edge_tts, "Communicate", Failing)
    with pytest.raises(common.IdeoError, match="synthèse vocale"):
        voice.EdgeTTSBackend().synthesize("x", "fr", tmp_path / "x.wav")


def test_get_backend_returns_edge():
    assert isinstance(voice.get_backend(), voice.EdgeTTSBackend)


@pytest.mark.network
def test_edge_backend_real_synthesis(tmp_path):
    out = tmp_path / "x.wav"
    voice.EdgeTTSBackend().synthesize("Bonjour, ceci est un test de voix.", "fr", out)
    with wave.open(str(out), "rb") as w:
        assert w.getframerate() == 48000 and w.getnchannels() == 1
        assert w.getnframes() / 48000 > 0.5


LANGS = ("fr", "en", "es", "de", "it", "pt", "nl", "pl", "tr", "ar", "ru", "ja", "ko", "zh", "hi")


def test_voice_table_covers_the_supported_languages():
    assert set(LANGS) <= set(voice.EDGE_VOICES)
    for lang, name in voice.EDGE_VOICES.items():
        assert name.startswith(f"{lang}-") and name.endswith("Neural")


def test_unsupported_language_message_lists_supported_ones():
    assert voice.unsupported("fr") is None
    message = voice.unsupported("sw")
    assert "« sw »" in message and "fr" in message and "ja" in message


@pytest.mark.network
def test_every_voice_exists_on_edge_tts():
    import asyncio

    import edge_tts

    names = {v["ShortName"] for v in asyncio.run(edge_tts.list_voices())}
    assert set(voice.EDGE_VOICES.values()) <= names
