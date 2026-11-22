import json
import stat

import pytest

from ideo import cle, common


def test_save_key_writes_private_env_and_engine(tmp_path):
    env_file = cle.save_key("  sk_test  ", tmp_path)
    assert env_file.read_text(encoding="utf-8") == "ELEVENLABS_API_KEY=sk_test\n"
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600
    assert json.loads((tmp_path / "config.json").read_text(encoding="utf-8")) == {"engine": "elevenlabs"}


def test_save_key_replaces_old_key_and_keeps_the_rest(tmp_path):
    (tmp_path / ".env").write_text("AUTRE=1\nELEVENLABS_API_KEY=old\n", encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps({"music": True, "elevenlabs_api_key": "old"}), encoding="utf-8")
    cle.save_key("sk_new", tmp_path)
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "AUTRE=1\nELEVENLABS_API_KEY=sk_new\n"
    assert json.loads((tmp_path / "config.json").read_text(encoding="utf-8")) == {"music": True, "engine": "elevenlabs"}


def test_empty_key_is_refused(tmp_path):
    with pytest.raises(common.IdeoError):
        cle.save_key("   ", tmp_path)
    assert not (tmp_path / ".env").exists()


def test_main_never_prints_the_key(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(cle.getpass, "getpass", lambda prompt: "sk_secret_123")
    monkeypatch.setattr(cle.eleven, "list_voices", lambda: [{"name": "A", "id": "1", "detail": ""}])
    assert cle.main() == 0
    assert "sk_secret_123" not in capsys.readouterr().out
