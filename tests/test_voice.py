import wave
from pathlib import Path

import pytest

from ideo import common, pacing, voice


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
    hook = common.load_json(paths[0].with_suffix(".words.json"))
    plan = common.load_json(job_with_plan / "plan.json")
    assert [w["w"] for w in hook] == voice.align.script_words(plan["parts"][0]["hook"])
    assert common.read_status(job_with_plan)["steps"]["voice-01"]["ok"] is True


def test_voice_part_texts_and_lang(job_with_plan, fake_backend, fake_whisper):
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    plan = common.load_json(job_with_plan / "plan.json")
    part = plan["parts"][0]
    assert fake_backend.calls[0][:2] == (voice.hookvoice.shape(part["hook"], "fr"), "fr")
    assert fake_backend.calls[1][0] == part["scenes"][0]["say"]
    assert fake_backend.calls[-1][0] == "Et toi, tu relis tes cours ou tu les oublies ? Si ça t'a plu, abonne-toi pour la prochaine !"
    assert all(lang == "fr" for _, lang in fake_whisper)


def test_voice_part_outro_next(job_with_plan, fake_backend, fake_whisper):
    set_next_part(job_with_plan)
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    assert fake_backend.calls[-1][0] == "Et toi, tu relis tes cours ou tu les oublies ? Si ça t'a plu, abonne-toi pour la partie deux : Le sommeil !"


def test_voice_part_outro_last_of_several_parts(job_with_plan, fake_backend, fake_whisper):
    set_next_part(job_with_plan)
    voice.voice_part(job_with_plan, 2, backend=fake_backend)
    assert fake_backend.calls[-1][0] == "Si ça t'a plu, abonne-toi pour la prochaine série !"


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
    assert fake_backend.calls[-1][0] == "Et toi, tu relis tes cours ou tu les oublies ? " + i18n_last("de")
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
        "fr": "fr-FR-RemyMultilingualNeural", "en": "en-US-GuyNeural", "es": "es-ES-AlvaroNeural",
        "de": "de-DE-ChristophNeural", "it": "it-IT-DiegoNeural", "pt": "pt-BR-AntonioNeural",
        "nl": "nl-NL-MaartenNeural", "pl": "pl-PL-MarekNeural", "tr": "tr-TR-AhmetNeural",
    }


def test_edge_backend_network_error_is_french(tmp_path, monkeypatch):
    import edge_tts

    class Failing:
        def __init__(self, text, voice, **kw):
            pass

        async def stream(self):
            raise OSError("down")
            yield

    monkeypatch.setattr(edge_tts, "Communicate", Failing)
    with pytest.raises(common.IdeoError, match="synthèse vocale"):
        voice.EdgeTTSBackend().synthesize("x", "fr", tmp_path / "x.wav")


def test_edge_backend_retries_when_no_audio_is_received(tmp_path, monkeypatch):
    import edge_tts

    calls = []

    class Flaky:
        def __init__(self, text, voice, **kw):
            calls.append(1)

        async def stream(self):
            if len(calls) < 3:
                raise edge_tts.exceptions.NoAudioReceived("No audio was received.")
            yield {"type": "audio", "data": b"mp3"}

    monkeypatch.setattr(edge_tts, "Communicate", Flaky)
    monkeypatch.setattr(voice.time, "sleep", lambda s: None)
    monkeypatch.setattr(voice, "_ffmpeg", lambda: "/usr/bin/true")
    voice.EdgeTTSBackend().synthesize("x", "fr", tmp_path / "x.wav")
    assert len(calls) == 3


def test_edge_backend_gives_up_after_three_attempts(tmp_path, monkeypatch):
    import edge_tts

    calls = []

    class Failing:
        def __init__(self, text, voice, **kw):
            calls.append(1)

        async def stream(self):
            raise OSError("down")
            yield

    monkeypatch.setattr(edge_tts, "Communicate", Failing)
    monkeypatch.setattr(voice.time, "sleep", lambda s: None)
    with pytest.raises(common.IdeoError, match="synthèse vocale"):
        voice.EdgeTTSBackend().synthesize("x", "fr", tmp_path / "x.wav")
    assert len(calls) == 3


def test_get_backend_returns_edge():
    assert isinstance(voice.get_backend(), voice.EdgeTTSBackend)


@pytest.mark.network
def test_edge_backend_real_synthesis(tmp_path):
    out = tmp_path / "x.wav"
    voice.EdgeTTSBackend().synthesize("Bonjour, ceci est un test de voix.", "fr", out)
    with wave.open(str(out), "rb") as w:
        assert w.getframerate() == 48000 and w.getnchannels() == 1
        assert w.getnframes() / 48000 > 0.5


LANGS = ("fr", "en", "es", "de", "it", "pt", "nl", "pl", "tr")
NON_LATIN = ("ar", "ru", "ja", "ko", "zh", "hi")


def test_voice_table_is_exactly_the_latin_script_languages():
    assert set(voice.EDGE_VOICES) == set(LANGS)
    for lang, name in voice.EDGE_VOICES.items():
        assert name.startswith(f"{lang}-") and name.endswith("Neural")


def test_unsupported_language_message_lists_supported_ones():
    assert voice.unsupported("fr") is None
    message = voice.unsupported("sw")
    assert "« sw »" in message and "fr, en, es, de, it, pt, nl, pl, tr" in message
    for lang in NON_LATIN:
        assert "alphabet latin" in voice.unsupported(lang)


@pytest.mark.network
def test_every_voice_exists_on_edge_tts():
    import asyncio

    import edge_tts

    names = {v["ShortName"] for v in asyncio.run(edge_tts.list_voices())}
    assert set(voice.EDGE_VOICES.values()) <= names


def test_voice_ffmpeg_failure_points_to_a_log_that_exists(job_with_plan, monkeypatch):
    import edge_tts

    class Writes:
        def __init__(self, text, voice, **kw):
            pass

        async def stream(self):
            yield {"type": "audio", "data": b"mp3"}

    monkeypatch.setattr(edge_tts, "Communicate", Writes)
    monkeypatch.setattr(voice.shutil, "which", lambda name: "/usr/bin/false")
    with pytest.raises(common.IdeoError) as exc:
        voice.voice_part(job_with_plan, 1)
    log = job_with_plan / "logs" / "voice-01.log"
    assert f"Voir {log}" in str(exc.value)
    assert log.exists()


class TimedBackend:
    def __init__(self, heard):
        self.heard = heard

    def synthesize(self, text, lang, out_wav):
        from tests.conftest import write_sine_wav

        write_sine_wav(out_wav, seconds=1.0)
        return self.heard


def test_boundaries_from_backend_skip_speech_recognition(job_with_plan, fake_whisper):
    heard = [{"w": "x", "s": 0.1, "e": 0.2}]
    voice.voice_part(job_with_plan, 1, backend=TimedBackend(heard))
    assert fake_whisper == []


def test_words_json_has_one_word_per_script_word_with_script_text(job_with_plan, fake_whisper):
    recognised = [{"w": "Sommalie", "s": 0.1, "e": 0.4}, {"w": "s", "s": 0.5, "e": 0.6}, {"w": "'entrancher", "s": 0.6, "e": 0.9}]
    voice.voice_part(job_with_plan, 1, backend=TimedBackend(recognised))
    plan = common.load_json(job_with_plan / "plan.json")
    say = plan["parts"][0]["scenes"][0]["say"]
    words = common.load_json(job_with_plan / "parts" / "01" / "seg_01.words.json")
    assert [w["w"] for w in words] == say.split()
    assert all(a["s"] <= b["s"] for a, b in zip(words, words[1:]))
    assert all(0 <= w["s"] <= w["e"] <= 1.0 + 1e-6 for w in words)


def test_edge_backend_requests_word_boundaries_and_default_rate(tmp_path, monkeypatch):
    import edge_tts

    seen = {}

    class Streams:
        def __init__(self, text, voice, **kw):
            seen.update(kw)

        async def stream(self):
            yield {"type": "WordBoundary", "offset": 1000000, "duration": 2000000, "text": "Bonjour"}
            yield {"type": "audio", "data": b"mp3"}

    monkeypatch.setattr(edge_tts, "Communicate", Streams)
    monkeypatch.setattr(voice, "_ffmpeg", lambda: "/usr/bin/true")
    words = voice.EdgeTTSBackend().synthesize("Bonjour", "fr", tmp_path / "x.wav")
    assert seen["rate"] == "+0%" and seen["boundary"] == "WordBoundary"
    assert words == [{"w": "Bonjour", "s": 0.1, "e": 0.3}]


def test_finish_segment_trims_silence_and_shifts_words(tmp_path):
    import numpy as np

    wav = tmp_path / "s.wav"
    rate = 48000
    t = np.arange(rate)
    pcm = np.concatenate([np.zeros(rate // 2), 8000 * np.sin(2 * np.pi * 440 * t / rate), np.zeros(rate)]).astype("<i2")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    words = voice.finish_segment(wav, "Un deux", [{"w": "Un", "s": 0.5, "e": 1.0}, {"w": "deux", "s": 1.0, "e": 1.5}])
    with wave.open(str(wav), "rb") as w:
        duration = w.getnframes() / rate
    assert duration == pytest.approx(1.06, abs=0.02)
    assert words[0]["s"] == pytest.approx(0.03, abs=0.02)
    assert words[-1]["e"] <= duration


def test_finish_segment_adds_a_pause_after_a_sentence_that_runs_into_the_next(tmp_path):
    import numpy as np

    wav = tmp_path / "s.wav"
    rate = 48000
    t = np.arange(rate)
    tone = 8000 * np.sin(2 * np.pi * 440 * t / rate)
    pcm = np.concatenate([tone, np.zeros(int(0.18 * rate)), tone]).astype("<i2")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    heard = [{"w": "grippe.", "s": 0.0, "e": 1.0}, {"w": "Entre", "s": 1.18, "e": 2.18}]
    words = voice.finish_segment(wav, "grippe. Entre", heard)
    with wave.open(str(wav), "rb") as w:
        duration = w.getnframes() / rate
    assert duration == pytest.approx(2.18 + (pacing.SENTENCE_GAP - 0.18), abs=0.05)
    assert words[1]["s"] - words[0]["e"] >= pacing.SENTENCE_GAP - 0.02


def test_finish_segment_pauses_after_a_question_mark_heard_as_a_word_of_its_own(tmp_path):
    import numpy as np

    wav = tmp_path / "s.wav"
    rate = 48000
    t = np.arange(rate)
    tone = 8000 * np.sin(2 * np.pi * 440 * t / rate)
    pcm = np.concatenate([tone, tone]).astype("<i2")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    heard = [{"w": "règles", "s": 0.0, "e": 0.85}, {"w": "?", "s": 0.85, "e": 1.0}, {"w": "Si", "s": 1.0, "e": 2.0}]
    words = voice.finish_segment(wav, "règles ? Si", heard)
    assert words[1]["s"] - words[0]["e"] >= pacing.SENTENCE_GAP - 0.02


def plan_with_numbers(job, say="En 1998, il y avait 3 000 personnes et 8 % de pluie."):
    plan = common.load_json(job / "plan.json")
    plan["parts"][0]["scenes"][0]["say"] = say
    common.save_json(job / "plan.json", plan)
    return say


def test_online_voice_receives_numbers_in_words_and_subtitles_keep_digits(job_with_plan, fake_backend, fake_whisper):
    say = plan_with_numbers(job_with_plan)
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    sent = fake_backend.calls[1][0]
    assert sent == "En mille neuf cent quatre-vingt-dix-huit, il y avait trois mille personnes et huit pour cent de pluie."
    words = common.load_json(job_with_plan / "parts" / "01" / "seg_01.words.json")
    assert [w["w"] for w in words] == voice.align.script_words(say) and "1998," in [w["w"] for w in words] and "3" in [w["w"] for w in words]
    assert all(a["s"] <= b["s"] for a, b in zip(words, words[1:]))
    assert (job_with_plan / "parts" / "01" / "seg_01.spoken.txt").read_text(encoding="utf-8") == sent


def test_one_original_word_spans_the_time_of_all_its_spoken_words(tmp_path):
    from tests.conftest import write_sine_wav

    wav = tmp_path / "s.wav"
    write_sine_wav(wav, seconds=3.0)
    text = "En 1998 oui"
    normalized = voice.numbers.normalize(text, "fr")
    heard = [{"w": w, "s": 0.2 + i * 0.3, "e": 0.2 + i * 0.3 + 0.25} for i, w in enumerate(normalized.text.split())]
    words = voice.finish_segment(wav, text, heard, normalized.text, normalized.units)
    assert [w["w"] for w in words] == ["En", "1998", "oui"]
    assert words[1]["s"] == pytest.approx(heard[1]["s"], abs=0.01) and words[1]["e"] == pytest.approx(heard[4]["e"], abs=0.01)
    assert words[2]["s"] >= words[1]["e"] - 0.01


def test_thousands_with_a_space_are_two_subtitle_words_sharing_one_span(tmp_path):
    from tests.conftest import write_sine_wav

    wav = tmp_path / "s.wav"
    write_sine_wav(wav, seconds=3.0)
    text = "Il y a 3 000 morts"
    normalized = voice.numbers.normalize(text, "fr")
    heard = [{"w": w, "s": 0.1 + i * 0.3, "e": 0.1 + i * 0.3 + 0.25} for i, w in enumerate(normalized.text.split())]
    words = voice.finish_segment(wav, text, heard, normalized.text, normalized.units)
    assert [w["w"] for w in words] == ["Il", "y", "a", "3", "000", "morts"]
    assert words[3]["s"] < words[3]["e"] <= words[4]["s"] + 1e-6 and words[4]["e"] == pytest.approx(heard[4]["e"], abs=0.01)


def test_only_segments_whose_sent_text_changes_are_redone(job_with_plan, fake_backend, fake_whisper):
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    first = len(fake_backend.calls)
    plan_with_numbers(job_with_plan)
    assert voice.stale(job_with_plan, 1) == ["seg_01"]
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    assert len(fake_backend.calls) == first + 1 and fake_backend.calls[-1][2] == "seg_01.wav"
    assert voice.stale(job_with_plan, 1) == []
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    assert len(fake_backend.calls) == first + 1


def test_segments_without_numbers_have_nothing_stale(job_with_plan, fake_backend, fake_whisper):
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    assert voice.stale(job_with_plan, 1) == []


def test_question_is_said_in_one_breath_with_the_call_to_subscribe(job_with_plan):
    plan = common.load_json(job_with_plan / "plan.json")
    segments = voice.segments(plan, plan["parts"][0])
    assert segments[-1] == ("seg_99_outro", "Et toi, tu relis tes cours ou tu les oublies ? Si ça t'a plu, abonne-toi pour la prochaine !")


def test_old_plan_without_question_still_produces(job_with_plan):
    plan = common.load_json(job_with_plan / "plan.json")
    plan["parts"][0].pop("question")
    assert voice.segments(plan, plan["parts"][0])[-1] == ("seg_99_outro", "Si ça t'a plu, abonne-toi pour la prochaine !")


def test_paid_voice_reuses_existing_segments_without_calling_the_service(job_with_plan, fake_backend, fake_whisper):
    voice.voice_part(job_with_plan, 1, backend=fake_backend)
    out_dir = job_with_plan / "parts" / "01"
    for name in out_dir.glob("*.spoken.txt"):
        name.unlink()

    class Paid:
        local = False
        paid = True
        characters = 0

        def synthesize(self, *args, **kwargs):
            raise AssertionError("un segment déjà payé ne doit pas être regénéré")

    voice.voice_part(job_with_plan, 1, backend=Paid())


def test_finish_segment_reprend_le_deux_points_du_texte_ecrit(tmp_path):
    import numpy as np

    from ideo import pacing

    wav = tmp_path / "s.wav"
    rate = 48000
    t = np.arange(rate)
    tone = 8000 * np.sin(2 * np.pi * 440 * t / rate)
    pcm = np.concatenate([tone, tone]).astype("<i2")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    heard = [{"w": "la", "s": 0.0, "e": 0.3}, {"w": "réduflation", "s": 0.3, "e": 1.0},
             {"w": "le", "s": 1.0, "e": 1.3}, {"w": "pot", "s": 1.3, "e": 2.0}]
    words = voice.finish_segment(wav, "la réduflation : le pot", heard)
    with wave.open(str(wav), "rb") as w:
        duration = w.getnframes() / rate
    assert duration == pytest.approx(2.0 + pacing.COLON_GAP, abs=0.02)
    assert words[2]["s"] == pytest.approx(1.0 + pacing.COLON_GAP, abs=0.02)


def test_finish_segment_garde_la_pause_de_fin_de_phrase_avec_des_mots_sans_ponctuation(tmp_path):
    import numpy as np

    wav = tmp_path / "s.wav"
    rate = 48000
    t = np.arange(rate)
    tone = 8000 * np.sin(2 * np.pi * 440 * t / rate)
    pcm = np.concatenate([tone, np.zeros(int(0.54 * rate)), tone]).astype("<i2")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    heard = [{"w": "quoi", "s": 0.0, "e": 1.0}, {"w": "Moi", "s": 1.54, "e": 2.54}]
    voice.finish_segment(wav, "C'est quoi ? Moi", heard)
    with wave.open(str(wav), "rb") as w:
        duration = w.getnframes() / rate
    assert duration >= 2.0 + 0.45 - 0.02


def test_the_question_and_the_subscribe_call_are_joined_with_a_pause(tmp_path):
    import numpy as np

    parts = []
    for k in range(2):
        path = tmp_path / f"p{k}.wav"
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(48000)
            w.writeframes((np.ones(48000) * 1000).astype("<i2").tobytes())
        parts.append(path)
    target = tmp_path / "joined.wav"
    starts = voice._join_wavs(parts, target)
    with wave.open(str(target), "rb") as w:
        total = w.getnframes() / 48000
    assert starts[1] == pytest.approx(1.0 + voice.JOIN_PAUSE)
    assert total == pytest.approx(2.0 + voice.JOIN_PAUSE)


class _PaidVoice:
    local = False
    paid = True

    def __init__(self):
        self.characters = 0

    def synthesize(self, text, lang, out_wav, previous_text=None, next_text=None):
        from conftest import write_sine_wav

        write_sine_wav(out_wav, seconds=1.0)
        self.characters += len(text)
        tokens = text.split()
        step = 1.0 / max(len(tokens), 1)
        return [{"w": t, "s": i * step, "e": (i + 0.9) * step} for i, t in enumerate(tokens)]


def test_paid_voice_retouches_questions_before_pacing(job_with_plan, fake_whisper, monkeypatch):
    from ideo import intonation

    seen = []

    def fake_adjust(wav, words, lang, hook=False):
        seen.append((wav.name, lang, hook))
        return ["« Pourquoi ? » : pic ajouté sur « pourquoi »"] if wav.stem == "seg_00_hook" else []

    monkeypatch.setattr(intonation, "adjust", fake_adjust)
    voice.voice_part(job_with_plan, 1, backend=_PaidVoice(), pay=True)
    hooks = {name: hook for name, _, hook in seen}
    assert hooks["seg_00_hook.wav"] is True
    assert not any(hook for name, hook in hooks.items() if name != "seg_00_hook.wav")
    assert all(lang == "fr" for _, lang, _ in seen)
    log = (job_with_plan / "logs" / "voice-01.log").read_text(encoding="utf-8")
    assert "seg_00_hook intonation retouchée" in log


def test_paid_voice_goes_on_without_praat(job_with_plan, fake_whisper, monkeypatch):
    from ideo import intonation

    def missing(wav, words, lang, hook=False):
        raise ImportError("parselmouth")

    monkeypatch.setattr(intonation, "adjust", missing)
    paths = voice.voice_part(job_with_plan, 1, backend=_PaidVoice(), pay=True)
    assert all(p.exists() for p in paths)
    log = (job_with_plan / "logs" / "voice-01.log").read_text(encoding="utf-8")
    assert "praat-parselmouth absent" in log
