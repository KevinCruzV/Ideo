import json
import sys
import types
import wave

import numpy as np
import pytest

from ideo import common, compact, transcribe

INFO = {"id": "abcdefghijk", "title": "T", "channel": "C", "webpage_url": "u",
        "duration": 40, "chapters": None, "language": "fr"}


def write_wav(path, seconds=40):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(np.zeros(16000 * seconds, dtype="<i2").tobytes())


def make_job(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    common.save_json(job / "info.json", INFO)
    write_wav(job / "source.wav")
    return job


def install_fake_model(monkeypatch, count, calls):
    def word(i):
        return types.SimpleNamespace(word=f" mot{i} ", start=i * 0.2, end=i * 0.2 + 0.15)

    class FakeModel:
        def __init__(self, name, device, compute_type):
            calls.append(("init", name, device, compute_type))

        def transcribe(self, pcm, **kwargs):
            calls.append(("transcribe", pcm.dtype, kwargs))
            seg = types.SimpleNamespace(words=[word(i) for i in range(count)])
            return iter([seg]), types.SimpleNamespace(language="fr")

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=FakeModel))


def test_transcribe_writes_words_and_lang(tmp_path, monkeypatch):
    job = make_job(tmp_path)
    calls = []
    install_fake_model(monkeypatch, 200, calls)
    words = transcribe.transcribe(job)
    assert len(words) == 200
    assert words[0] == {"w": "mot0", "s": 0.0, "e": 0.15}
    assert common.load_json(job / "words.json") == words
    assert (job / "lang.txt").read_text().strip() == "fr"
    assert common.read_status(job)["steps"]["transcribe"]["ok"] is True
    assert calls[0] == ("init", "small", "cpu", "int8")
    assert calls[1][1] == np.float32
    assert calls[1][2]["word_timestamps"] is True and calls[1][2]["vad_filter"] is True


def test_transcribe_is_idempotent(tmp_path, monkeypatch):
    job = make_job(tmp_path)
    calls = []
    install_fake_model(monkeypatch, 200, calls)
    first = transcribe.transcribe(job)
    n = len(calls)
    assert transcribe.transcribe(job) == first
    assert len(calls) == n


def test_too_little_speech_raises(tmp_path, monkeypatch):
    job = make_job(tmp_path)
    install_fake_model(monkeypatch, 40, [])
    with pytest.raises(common.IdeoError, match="pas assez de parole"):
        transcribe.transcribe(job)
    assert common.read_status(job)["steps"]["transcribe"]["ok"] is False
    assert not (job / "words.json").exists()


def test_retry_after_failure_transcribes_again(tmp_path, monkeypatch):
    job = make_job(tmp_path)
    install_fake_model(monkeypatch, 40, [])
    with pytest.raises(common.IdeoError):
        transcribe.transcribe(job)
    install_fake_model(monkeypatch, 200, [])
    assert len(transcribe.transcribe(job)) == 200


def test_prepare_transcript(tmp_path, monkeypatch):
    job = make_job(tmp_path)
    install_fake_model(monkeypatch, 200, [])
    transcribe.transcribe(job)
    result = compact.prepare_transcript(job)
    assert result["words"] == 200 and result["lang"] == "fr"
    assert result["paragraphs"] >= 1 and result["sfx"] == 0
    assert (job / "sfx.json").exists()
    text = (job / "transcript_compact.md").read_text(encoding="utf-8")
    assert "mot0" in text
    assert common.read_status(job)["steps"]["transcript"]["ok"] is True
    assert compact.prepare_transcript(job) == result


@pytest.mark.slow
@pytest.mark.network
def test_real_transcription_of_synthetic_speech(tmp_path):
    import shutil
    import subprocess
    if not shutil.which("say") or not shutil.which("ffmpeg"):
        pytest.skip("say ou ffmpeg indisponible")
    job = make_job(tmp_path)
    aiff = tmp_path / "s.aiff"
    subprocess.run(["say", "-o", str(aiff), "The quick brown fox jumps over the lazy dog near the river bank."], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", str(aiff), "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                    str(job / "source.wav")], check=True, capture_output=True)
    words = transcribe.transcribe(job, min_words=3)
    text = " ".join(w["w"] for w in words).lower()
    assert "fox" in text and (job / "lang.txt").read_text().strip() == "en"
