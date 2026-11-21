import json

import pytest

from ideo import common, config, voice


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    return tmp_path


def write(home, content):
    (home / "config.json").write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")


def test_missing_file_gives_defaults():
    assert config.voice_for("fr") == "fr-FR-RemyMultilingualNeural"
    assert config.rate() == "+0%"


def test_voices_replace_defaults_per_language(home):
    write(home, {"voices": {"fr": "fr-FR-DeniseNeural"}})
    assert config.voice_for("fr") == "fr-FR-DeniseNeural"
    assert config.voice_for("en") == voice.EDGE_VOICES["en"]
    assert config.rate() == "+0%"


def test_rate_key(home):
    write(home, {"rate": "+8%"})
    assert config.rate() == "+8%"
    assert config.voice_for("de") == voice.EDGE_VOICES["de"]


def test_invalid_json_is_a_clear_french_error(home):
    write(home, "{pas du json")
    with pytest.raises(common.IdeoError, match="config.json n'est pas un JSON valide"):
        config.rate()


@pytest.mark.parametrize("content", [
    [1], {"voices": "fr"}, {"voices": {"fr": 3}}, {"rate": 8}, {"rate": "vite"}, {"voices": {"fr": ""}},
])
def test_wrong_shapes_are_clear_french_errors(home, content):
    write(home, content)
    with pytest.raises(common.IdeoError, match="config.json"):
        config.rate()


def test_voice_module_uses_the_config(home, monkeypatch, tmp_path):
    import edge_tts

    write(home, {"voices": {"fr": "fr-FR-DeniseNeural"}, "rate": "+3%"})
    seen = {}

    class Streams:
        def __init__(self, text, name, **kw):
            seen["voice"] = name
            seen.update(kw)

        async def stream(self):
            yield {"type": "audio", "data": b"mp3"}

    monkeypatch.setattr(edge_tts, "Communicate", Streams)
    monkeypatch.setattr(voice, "_ffmpeg", lambda: "/usr/bin/true")
    voice.EdgeTTSBackend().synthesize("Bonjour", "fr", tmp_path / "x.wav")
    assert seen["voice"] == "fr-FR-DeniseNeural" and seen["rate"] == "+3%"


def test_gitignore_lists_config():
    assert "config.json" in (common.REPO_ROOT / ".gitignore").read_text(encoding="utf-8").split()


def test_part_hash_changes_with_the_voice_and_the_rate(home, job_with_fixtures):
    from ideo import pipeline

    plan = common.load_json(job_with_fixtures / "plan.json")
    part = plan["parts"][0]
    before = pipeline.part_hash(plan, part)
    write(home, {"rate": "+5%"})
    assert pipeline.part_hash(plan, part) != before
    write(home, {"voices": {"fr": "fr-FR-DeniseNeural"}})
    assert pipeline.part_hash(plan, part) != before
