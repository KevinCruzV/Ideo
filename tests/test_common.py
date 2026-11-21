import pytest

from ideo import common


def test_job_dir_uses_youtube_id(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    d = common.job_dir("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10")
    assert d == tmp_path / "jobs" / "dQw4w9WgXcQ" and d.is_dir()
    assert common.job_dir("https://youtu.be/dQw4w9WgXcQ") == d
    assert common.job_dir("https://www.youtube.com/shorts/dQw4w9WgXcQ") == d


def test_job_dir_rejects_non_youtube(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    with pytest.raises(common.IdeoError):
        common.job_dir("https://example.com/video")


def test_mark_and_read_status(tmp_path):
    assert common.read_status(tmp_path) == {"steps": {}}
    common.mark(tmp_path, "fetch", True, "ok")
    common.mark(tmp_path, "pick", False, "boom")
    steps = common.read_status(tmp_path)["steps"]
    assert steps["fetch"]["ok"] is True
    assert steps["fetch"]["detail"] == "ok"
    assert steps["pick"]["ok"] is False
    assert "at" in steps["fetch"]


def test_run_raises_readable_error(tmp_path):
    with pytest.raises(common.IdeoError):
        common.run(["false"], tmp_path / "x.log")


def test_run_logs_output(tmp_path):
    log = tmp_path / "x.log"
    common.run(["echo", "hello"], log)
    assert "hello" in log.read_text()


def test_json_roundtrip(tmp_path):
    common.save_json(tmp_path / "a.json", {"é": 1})
    assert common.load_json(tmp_path / "a.json") == {"é": 1}


def test_timestamps():
    assert common.parse_ts("12:30") == 750.0
    assert common.parse_ts("1:02:03") == 3723.0
    assert common.fmt_ts(3723.4) == "1:02:03"
    assert common.fmt_ts(75) == "1:15"
