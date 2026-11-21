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


def test_entretien_defaults():
    assert config.entretien_auto() is True
    assert config.entretien_seuil() == 5


def test_entretien_keys(home):
    write(home, {"entretien_auto": False, "entretien_seuil": 3})
    assert config.entretien_auto() is False and config.entretien_seuil() == 3


@pytest.mark.parametrize("content", [
    {"entretien_auto": "oui"}, {"entretien_auto": 1}, {"entretien_seuil": "5"}, {"entretien_seuil": 0},
    {"entretien_seuil": True}, {"entretien_seuil": 2.5},
])
def test_entretien_keys_wrong_types(home, content):
    write(home, content)
    with pytest.raises(common.IdeoError, match="config.json"):
        config.entretien_auto()


def test_engine_defaults_to_kyutai_only_when_available(monkeypatch):
    monkeypatch.setattr(config, "kyutai_available", lambda: True)
    assert config.engine() == "kyutai"
    monkeypatch.setattr(config, "kyutai_available", lambda: False)
    assert config.engine() == "edge"


def test_engine_key_overrides_the_default(home, monkeypatch):
    monkeypatch.setattr(config, "kyutai_available", lambda: False)
    write(home, {"engine": "kyutai"})
    assert config.engine() == "kyutai"
    monkeypatch.setattr(config, "kyutai_available", lambda: True)
    write(home, {"engine": "edge"})
    assert config.engine() == "edge"


@pytest.mark.parametrize("content", [{"engine": "autre"}, {"engine": 3}, {"kyutai_voice": ""}, {"kyutai_voice": 3},
                                     {"kyutai_padding_bonus": "1"}, {"kyutai_padding_bonus": 3}, {"kyutai_padding_bonus": -2.5},
                                     {"kyutai_padding_bonus": True}])
def test_voice_engine_keys_wrong_values(home, content):
    write(home, content)
    with pytest.raises(common.IdeoError, match="config.json"):
        config.engine()


def test_kyutai_defaults_and_keys(home):
    assert config.kyutai_voice() == "unmute-prod-website/developpeuse-3.wav"
    assert config.kyutai_padding_bonus() == 0.5
    write(home, {"kyutai_voice": "autre/voix.wav", "kyutai_padding_bonus": -1})
    assert config.kyutai_voice() == "autre/voix.wav" and config.kyutai_padding_bonus() == -1


def make_env(root):
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "python").write_text("", encoding="utf-8")
    (root / "lib" / "python3.12" / "site-packages" / "moshi_mlx").mkdir(parents=True)


def test_installed_needs_interpreter_package_and_no_install_in_progress(monkeypatch, tmp_path):
    env = tmp_path / ".venv-voix2"
    monkeypatch.undo()
    monkeypatch.setattr(config, "KYUTAI_PYTHON", env / "bin" / "python")
    assert config.kyutai_installed() is False
    (env / "bin").mkdir(parents=True)
    (env / "bin" / "python").write_text("", encoding="utf-8")
    assert config.kyutai_installed() is False
    (env / "lib" / "python3.12" / "site-packages" / "moshi_mlx").mkdir(parents=True)
    assert config.kyutai_installed() is True
    config.install_lock().write_text("", encoding="utf-8")
    assert config.kyutai_installed() is False


def test_available_also_needs_apple_silicon(monkeypatch, tmp_path):
    import platform

    env = tmp_path / ".venv-voix2"
    make_env(env)
    monkeypatch.undo()
    monkeypatch.setattr(config, "KYUTAI_PYTHON", env / "bin" / "python")
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    assert config.kyutai_available() is True
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    assert config.kyutai_available() is False


def test_local_voice_missing(monkeypatch, home):
    monkeypatch.setattr(config, "apple_silicon", lambda: True)
    monkeypatch.setattr(config, "kyutai_installed", lambda: False)
    assert config.local_voice_missing("fr") is True and config.local_voice_missing("en") is True
    assert config.local_voice_missing("de") is False
    write(home, {"engine": "edge"})
    assert config.local_voice_missing("fr") is False
    write(home, {"engine": "kyutai"})
    assert config.local_voice_missing("fr") is True
    monkeypatch.setattr(config, "kyutai_installed", lambda: True)
    assert config.local_voice_missing("fr") is False
    monkeypatch.setattr(config, "kyutai_installed", lambda: False)
    monkeypatch.setattr(config, "apple_silicon", lambda: False)
    assert config.local_voice_missing("fr") is False


def test_hook_settings_defaults_and_keys(home):
    assert config.kyutai_hook_temp() == 0.9 and config.kyutai_hook_padding_bonus() == 0
    write(home, {"kyutai_hook_temp": 1.0, "kyutai_hook_padding_bonus": 0.5})
    assert config.kyutai_hook_temp() == 1.0 and config.kyutai_hook_padding_bonus() == 0.5


@pytest.mark.parametrize("content", [{"kyutai_hook_temp": 0}, {"kyutai_hook_temp": 2}, {"kyutai_hook_temp": "0.9"},
                                     {"kyutai_hook_temp": True}, {"kyutai_hook_padding_bonus": 3},
                                     {"kyutai_hook_padding_bonus": "0"}])
def test_hook_settings_wrong_values(home, content):
    write(home, content)
    with pytest.raises(common.IdeoError, match="config.json"):
        config.engine()
