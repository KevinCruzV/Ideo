import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import json
import shutil

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def isolated_home(tmp_path_factory, monkeypatch):
    from ideo import config

    monkeypatch.setenv("IDEO_HOME", str(tmp_path_factory.mktemp("ideo-home")))
    monkeypatch.setenv("IDEO_LOOPS", str(tmp_path_factory.mktemp("no-loops")))
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setattr(config, "kyutai_available", lambda: False)
    monkeypatch.setattr(config, "kyutai_installed", lambda: False)
    monkeypatch.setattr(config, "apple_silicon", lambda: False)


@pytest.fixture
def job_with_fixtures(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    shutil.copy(FIXTURES / "words_small.json", job / "words.json")
    shutil.copy(FIXTURES / "plan_ok.json", job / "plan.json")
    (job / "lang.txt").write_text("fr", encoding="utf-8")
    (job / "sfx.json").write_text(
        json.dumps([{"at": "1:10", "s": 70.0, "e": 72.5}]), encoding="utf-8"
    )
    (job / "info.json").write_text(json.dumps({"duration": 120}), encoding="utf-8")
    return job


import math
import wave


def write_sine_wav(path, seconds=0.6, rate=48000, frequency=440):
    n = int(rate * seconds)
    frames = b"".join(
        int(8000 * math.sin(2 * math.pi * frequency * i / rate)).to_bytes(2, "little", signed=True) for i in range(n)
    )
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames)


class FakeBackend:
    def __init__(self):
        self.calls = []

    def synthesize(self, text, lang, out_wav):
        self.calls.append((text, lang, Path(out_wav).name))
        write_sine_wav(out_wav)


@pytest.fixture
def job_with_plan(job_with_fixtures):
    return job_with_fixtures


@pytest.fixture
def fake_backend():
    return FakeBackend()


@pytest.fixture
def fake_whisper(monkeypatch):
    from ideo import voice

    calls = []

    def fake(wav, lang, log=None):
        calls.append((Path(wav).name, lang))
        return [{"w": "mot", "s": 0.0, "e": 0.3}]

    monkeypatch.setattr(voice, "retranscribe", fake)
    return calls


VOICE_DURATIONS = {
    "seg_00_hook": 0.8,
    "seg_01": 1.0,
    "seg_02": 1.0,
    "seg_03": 1.0,
    "seg_04": 1.0,
    "seg_05": 0.6,
    "seg_99_outro": 0.8,
}

VOICE_WORDS = {
    "seg_00_hook": ["Dis-moi", "pourquoi", "tu", "oublies", "ce", "que", "tu", "viens", "de", "lire", "?"],
    "seg_01": ["Aujourd'hui", "nous", "allons", "comprendre", "pourquoi", "on", "oublie."],
    "seg_02": ["Le", "lundi", "tout", "est", "clair", "dans", "la", "tête,", "mais", "dès", "le", "quatrième", "jour",
               "rien."],
    "seg_03": ["Il", "y", "a", "plus", "de", "cent", "ans."],
    "seg_04": ["Heureusement", "il", "existe", "des", "gestes", "simples."],
    "seg_05": ["Voici", "son", "résultat."],
    "seg_99_outro": ["Et", "toi,", "tu", "relis", "tes", "cours", "ou", "tu", "les", "oublies\u00a0?", "Abonne-toi", "pour", "la", "suite."],
}


def _timed_words(words, duration):
    step = duration / len(words)
    return [{"w": w, "s": round(i * step, 3), "e": round(i * step + step * 0.8, 3)} for i, w in enumerate(words)]


def write_silence_wav(path, seconds, rate=16000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(2 * int(rate * seconds)))


@pytest.fixture
def job_with_voice_fixtures(job_with_fixtures):
    from ideo import common

    job = job_with_fixtures
    part_dir = job / "parts" / "01"
    part_dir.mkdir(parents=True)
    for name, duration in VOICE_DURATIONS.items():
        write_sine_wav(part_dir / f"{name}.wav", seconds=duration)
        common.save_json(part_dir / f"{name}.words.json", _timed_words(VOICE_WORDS[name], duration))
    write_silence_wav(job / "source.wav", 80.0)
    return job


@pytest.fixture
def job_with_offsets(job_with_voice_fixtures):
    from ideo import assemble

    assemble.assemble_part(job_with_voice_fixtures, 1)
    return job_with_voice_fixtures
