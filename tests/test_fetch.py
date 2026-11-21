import json

import pytest

from ideo import common, fetch

URL = "https://youtu.be/abcdefghijk"


@pytest.mark.parametrize("stderr,expected", [
    ("ERROR: [youtube] x: Private video", "vidéo privée"),
    ("ERROR: [youtube] x: Video unavailable", "indisponible"),
    ("ERROR: Sign in to confirm your age", "restriction d'âge"),
    ("ERROR: [youtube] x: This live event will begin", "en direct"),
])
def test_explain_ytdlp_error(stderr, expected):
    assert expected in fetch.explain_ytdlp_error(stderr)


def test_explain_unknown_error_keeps_last_line():
    assert "boom" in fetch.explain_ytdlp_error("noise\nERROR: boom")


def fake_run_ok(calls):
    def fake(cmd, log):
        calls.append(cmd)
        if "yt_dlp" in " ".join(cmd):
            out = cmd[cmd.index("-o") + 1]
            base = out.replace(".%(ext)s", "")
            open(base + ".m4a", "wb").write(b"m4a")
            open(base + ".info.json", "w", encoding="utf-8").write(json.dumps({
                "id": "abcdefghijk", "title": "T", "channel": "C",
                "webpage_url": URL, "duration": 42, "chapters": None,
                "language": "fr", "extra": "ignored",
            }))
        else:
            open(cmd[-1], "wb").write(b"wav")
    return fake


def test_fetch_success_writes_outputs_and_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(fetch.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    calls = []
    monkeypatch.setattr(common, "run", fake_run_ok(calls))
    job = fetch.fetch(URL)
    assert job == tmp_path / "jobs" / "abcdefghijk"
    assert (job / "source.wav").read_bytes() == b"wav"
    assert (job / "source.m4a").read_bytes() == b"m4a"
    info = common.load_json(job / "info.json")
    assert info == {
        "id": "abcdefghijk", "title": "T", "channel": "C", "webpage_url": URL,
        "duration": 42, "chapters": [], "language": "fr",
    }
    assert common.read_status(job)["steps"]["fetch"]["ok"] is True
    ffmpeg_cmd = calls[1]
    assert ffmpeg_cmd[0] == "/usr/bin/ffmpeg"
    assert ["-ac", "1", "-ar", "16000"] == ffmpeg_cmd[ffmpeg_cmd.index("-ac"):ffmpeg_cmd.index("-ac") + 4]
    assert not list(job.glob(".fetch-*"))
    n = len(calls)
    assert fetch.fetch(URL) == job
    assert len(calls) == n


def test_failed_fetch_marks_status_not_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(fetch.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    def fake(cmd, log):
        raise common.IdeoError("ERROR: Private video")

    monkeypatch.setattr(common, "run", fake)
    job = common.job_dir(URL)
    with pytest.raises(common.IdeoError) as exc:
        fetch.fetch(URL)
    assert "vidéo privée" in str(exc.value)
    assert common.read_status(job)["steps"]["fetch"]["ok"] is False
    assert not (job / "source.wav").exists()
    assert not list(job.glob(".fetch-*"))


def test_fetch_without_ffmpeg_fails_readably(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(fetch.shutil, "which", lambda name: None)
    job = common.job_dir(URL)
    with pytest.raises(common.IdeoError) as exc:
        fetch.fetch(URL)
    assert "ffmpeg" in str(exc.value)
    assert common.read_status(job)["steps"]["fetch"]["ok"] is False


@pytest.mark.network
def test_fetch_real_short_video(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    job = fetch.fetch("https://www.youtube.com/watch?v=jNQXAC9IVRw")
    info = common.load_json(job / "info.json")
    assert info["id"] == "jNQXAC9IVRw"
    assert info["duration"] < 60
    assert set(info) == {"id", "title", "channel", "webpage_url", "duration", "chapters", "language"}
    assert (job / "source.wav").stat().st_size > 10000
    assert (job / "source.m4a").stat().st_size > 1000
    assert common.read_status(job)["steps"]["fetch"]["ok"] is True
