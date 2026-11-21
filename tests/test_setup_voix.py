import json
from pathlib import Path

import pytest

from ideo import cli, common, config, setup_voix
from tests.conftest import write_sine_wav


@pytest.fixture
def env(monkeypatch, tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setenv("IDEO_HOME", str(root))
    monkeypatch.setattr(config, "KYUTAI_PYTHON", root / ".venv-voix2" / "bin" / "python")
    monkeypatch.setattr(config, "apple_silicon", lambda: True)
    monkeypatch.setattr(config, "kyutai_installed", lambda: (root / ".venv-voix2" / "ready").exists()
                        and not config.install_lock().exists())
    calls = []

    def fake_run(cmd, log):
        cmd = [str(c) for c in cmd]
        calls.append(cmd)
        tools, venv = root / ".venv-tools", root / ".venv-voix2"
        if cmd[1:3] == ["-m", "venv"]:
            (tools / "bin").mkdir(parents=True)
            (tools / "bin" / "python").write_text("", encoding="utf-8")
        elif cmd[1:3] == ["install", "-q"]:
            (tools / "bin" / "uv").write_text("", encoding="utf-8")
        elif cmd[1] == "venv":
            (venv / "bin").mkdir(parents=True)
            (venv / "bin" / "python").write_text("", encoding="utf-8")
        elif cmd[1:3] == ["pip", "install"]:
            (venv / "lib" / "python3.12" / "site-packages" / "moshi_mlx").mkdir(parents=True)
            (venv / "ready").write_text("", encoding="utf-8")
        elif "moshi_mlx.run_tts" in cmd:
            if getattr(fake_run, "silent", False):
                return
            out = Path(cmd[cmd.index("--out-folder") + 1])
            out.mkdir(parents=True, exist_ok=True)
            write_sine_wav(out / "check.wav", seconds=0.3, rate=24000)
        if getattr(fake_run, "fail_on", None) and fake_run.fail_on in " ".join(cmd):
            raise common.IdeoError("La commande a échoué (code 1)")

    monkeypatch.setattr(common, "run", fake_run)
    fake_run.calls = calls
    fake_run.root = root
    return fake_run


def test_not_apple_silicon(env, monkeypatch, capsys):
    monkeypatch.setattr(config, "apple_silicon", lambda: False)
    assert cli.main(["setup-voix"]) == 1
    assert capsys.readouterr().out.strip() == ("ERREUR setup-voix : la voix locale demande un Mac à puce Apple. "
                                               "La voix en ligne sera utilisée.")
    assert env.calls == []


def test_cold_install_runs_the_commands_in_order_and_reports_the_duration(env, capsys):
    assert cli.main(["setup-voix"]) == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("OK setup-voix : voix locale prête (") and out.endswith(")")
    flat = [" ".join(c) for c in env.calls]
    assert "-m venv" in flat[0] and ".venv-tools" in flat[0]
    assert flat[1].endswith("install -q uv")
    assert "uv venv --python 3.12" in flat[2] and flat[2].endswith(".venv-voix2")
    assert "uv pip install --python" in flat[3] and flat[3].endswith("moshi_mlx")
    assert "snapshot_download" in flat[4] and "kyutai/tts-1.6b-en_fr" in flat[4] and "developpeuse-3.wav" in flat[4]
    assert "moshi_mlx.run_tts" in flat[5] and "--only-wav" in flat[5]


def test_marker_records_the_voice(env):
    setup_voix.run()
    assert common.load_json(env.root / ".venv-voix2" / "ideo-voix.json")["voice"] == config.kyutai_voice()
    assert not config.install_lock().exists()


def test_second_run_does_nothing(env, capsys):
    setup_voix.run()
    count = len(env.calls)
    assert cli.main(["setup-voix"]) == 0
    assert "déjà prête" in capsys.readouterr().out and len(env.calls) == count


def test_changing_the_voice_downloads_again_without_reinstalling(env):
    setup_voix.run()
    count = len(env.calls)
    (env.root / "config.json").write_text(json.dumps({"kyutai_voice": "autre/voix.wav"}), encoding="utf-8")
    setup_voix.run()
    new = [" ".join(c) for c in env.calls[count:]]
    assert len(new) == 2 and "autre/voix.wav" in new[0] and "moshi_mlx.run_tts" in new[1]


def test_existing_environment_without_marker_is_verified_not_rebuilt(env):
    (env.root / ".venv-voix2" / "bin").mkdir(parents=True)
    (env.root / ".venv-voix2" / "bin" / "python").write_text("", encoding="utf-8")
    (env.root / ".venv-voix2" / "lib" / "python3.12" / "site-packages" / "moshi_mlx").mkdir(parents=True)
    (env.root / ".venv-voix2" / "ready").write_text("", encoding="utf-8")
    (env.root / ".venv-tools" / "bin").mkdir(parents=True)
    (env.root / ".venv-tools" / "bin" / "python").write_text("", encoding="utf-8")
    (env.root / ".venv-tools" / "bin" / "uv").write_text("", encoding="utf-8")
    setup_voix.run()
    assert [("run_tts" in " ".join(c) or "snapshot_download" in " ".join(c)) for c in env.calls] == [True, True]


def test_a_failed_step_gives_a_clear_error_and_clears_the_lock(env, capsys):
    env.fail_on = "uv pip install"
    assert cli.main(["setup-voix"]) == 1
    out = capsys.readouterr().out.strip()
    assert out.startswith("ERREUR setup-voix : l'installation de moshi_mlx a échoué") and "setup-voix" in out
    assert "engine" in out and not config.install_lock().exists()


def test_silent_verification_is_an_error(env, capsys):
    env.silent = True
    assert cli.main(["setup-voix"]) == 1
    assert "n'a rien produit" in capsys.readouterr().out
    assert not (env.root / ".venv-voix2" / "ideo-voix.json").exists()


def test_lock_is_present_during_the_install(env):
    seen = []
    base = common.run

    def watching(cmd, log):
        seen.append(config.install_lock().exists())
        base(cmd, log)

    common.run = watching
    try:
        setup_voix.run()
    finally:
        common.run = base
    assert seen and all(seen[:-1])


def test_log_lives_at_the_root_logs(env):
    assert setup_voix.log_path() == env.root / "logs" / "setup-voix.log"


@pytest.mark.parametrize("gigabytes,text", [(4.45, "4,5"), (4.2, "4"), (4.3, "4,5"), (5.0, "5"), (3.74, "3,5")])
def test_size_is_rounded_to_the_half_gigabyte(gigabytes, text):
    assert setup_voix.size_text(gigabytes) == text


def test_install_note_only_when_the_local_voice_is_missing_and_possible(env):
    assert setup_voix.install_note("fr") == f" Voix locale : à installer (environ {setup_voix.size_text()} Go)."
    assert setup_voix.install_note("de") == ""
    (env.root / "config.json").write_text('{"engine": "edge"}', encoding="utf-8")
    assert setup_voix.install_note("fr") == ""


def test_install_note_is_empty_when_installed_or_not_apple_silicon(env, monkeypatch):
    monkeypatch.setattr(config, "kyutai_installed", lambda: True)
    assert setup_voix.install_note("fr") == ""
    monkeypatch.setattr(config, "kyutai_installed", lambda: False)
    monkeypatch.setattr(config, "apple_silicon", lambda: False)
    assert setup_voix.install_note("fr") == ""


def test_prepare_line_ends_with_the_install_note(env, monkeypatch, capsys):
    from ideo import compact, fetch, transcribe

    url = "https://www.youtube.com/watch?v=abcdefghijk"
    monkeypatch.setattr(fetch, "fetch", lambda u: common.job_dir(u))
    monkeypatch.setattr(transcribe, "transcribe", lambda job: [{"w": "a", "s": 0, "e": 1}] * 300)
    monkeypatch.setattr(compact, "prepare_transcript", lambda job: {"words": 300, "paragraphs": 7, "sfx": 1, "lang": "fr"})
    assert cli.main(["prepare", url]) == 0
    line = capsys.readouterr().out.strip().splitlines()[0]
    assert line.endswith(" Voix locale : à installer (environ 4,5 Go).")
    (env.root / ".venv-voix2" / "ready").parent.mkdir(parents=True, exist_ok=True)
    (env.root / ".venv-voix2" / "ready").write_text("", encoding="utf-8")
    (env.root / ".venv-voix2" / "bin").mkdir(parents=True, exist_ok=True)
    cli.main(["prepare", url])
    assert "Voix locale" not in capsys.readouterr().out
