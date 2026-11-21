import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import json
import shutil

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


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


def write_sine_wav(path, seconds=0.6, rate=48000):
    n = int(rate * seconds)
    frames = b"".join(
        int(8000 * math.sin(2 * math.pi * 440 * i / rate)).to_bytes(2, "little", signed=True) for i in range(n)
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

    def fake(wav, lang):
        calls.append((Path(wav).name, lang))
        return [{"w": "mot", "s": 0.0, "e": 0.3}]

    monkeypatch.setattr(voice, "retranscribe", fake)
    return calls
