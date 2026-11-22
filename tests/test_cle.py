import json
import stat

import pytest

from ideo import cle, common


def test_save_key_creates_private_config(tmp_path):
    path = tmp_path / "config.json"
    cle.save_key("  sk_test  ", path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"elevenlabs_api_key": "sk_test", "engine": "elevenlabs"}
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_save_key_keeps_other_settings(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"music": True, "engine": "kyutai"}), encoding="utf-8")
    cle.save_key("sk_new", path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"music": True, "engine": "elevenlabs", "elevenlabs_api_key": "sk_new"}


def test_empty_key_is_refused(tmp_path):
    path = tmp_path / "config.json"
    with pytest.raises(common.IdeoError):
        cle.save_key("   ", path)
    assert not path.exists()


def test_main_never_prints_the_key(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(cle.getpass, "getpass", lambda prompt: "sk_secret_123")
    monkeypatch.setattr(cle.eleven, "list_voices", lambda: [{"name": "A", "id": "1", "detail": ""}])
    assert cle.main() == 0
    assert "sk_secret_123" not in capsys.readouterr().out
