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
        "duration": 42, "chapters": [], "language": "fr", "skip": [],
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


def test_fetch_surfaces_real_ytdlp_error_line(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(fetch.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    def fake(cmd, log):
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "ab") as f:
            f.write(b"[youtube] x: Downloading\nERROR: [youtube] x: Something odd happened\n")
        raise common.IdeoError("La commande a échoué (code 1) : yt-dlp. Voir log")

    monkeypatch.setattr(common, "run", fake)
    with pytest.raises(common.IdeoError) as exc:
        fetch.fetch(URL)
    assert "Something odd happened" in str(exc.value)
    assert "code 1" not in str(exc.value)


def test_format_not_available_is_not_unavailable_video():
    message = fetch.explain_ytdlp_error("ERROR: [youtube] x: Requested format is not available")
    assert "indisponible" not in message
    assert "Requested format is not available" in message


def test_non_ideo_error_marks_status_and_wraps(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(fetch.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    def fake(cmd, log):
        if "yt_dlp" in " ".join(cmd):
            base = cmd[cmd.index("-o") + 1].replace(".%(ext)s", "")
            open(base + ".m4a", "wb").write(b"m4a")
            open(base + ".info.json", "w").write("{not json")

    monkeypatch.setattr(common, "run", fake)
    job = common.job_dir(URL)
    with pytest.raises(common.IdeoError) as exc:
        fetch.fetch(URL)
    assert "Erreur inattendue" in str(exc.value)
    assert common.read_status(job)["steps"]["fetch"]["ok"] is False
    assert not list(job.glob(".fetch-*"))


def test_retry_removes_stale_wav(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(fetch.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    job = common.job_dir(URL)
    (job / "source.wav").write_bytes(b"stale")
    common.mark(job, "fetch", False, "x")

    def fake(cmd, log):
        raise common.IdeoError("ERROR: Private video")

    monkeypatch.setattr(common, "run", fake)
    with pytest.raises(common.IdeoError):
        fetch.fetch(URL)
    assert not (job / "source.wav").exists()


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


def fake_run_sponsor(calls, fail_sponsorblock=False):
    def fake(cmd, log):
        calls.append(cmd)
        if "yt_dlp" not in " ".join(cmd):
            open(cmd[-1], "wb").write(b"wav")
            return
        if fail_sponsorblock and "--sponsorblock-mark" in cmd:
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "a", encoding="utf-8") as f:
                f.write("ERROR: Postprocessing: Unable to communicate with SponsorBlock API\n")
            raise common.IdeoError("code 1")
        base = cmd[cmd.index("-o") + 1].replace(".%(ext)s", "")
        open(base + ".m4a", "wb").write(b"m4a")
        raw = {"id": "abcdefghijk", "title": "T", "channel": "C", "webpage_url": URL, "duration": 1145,
               "chapters": [{"start_time": 0, "end_time": 62, "title": "Intro"}], "language": "en"}
        if "--sponsorblock-mark" in cmd:
            raw["sponsorblock_chapters"] = [
                {"start_time": 0, "end_time": 5.48, "category": "sponsor", "title": "Sponsor", "type": "skip"},
                {"start_time": 1027.3, "end_time": 1145, "category": "selfpromo", "title": "Self", "type": "skip"},
                {"start_time": 400, "end_time": 400, "category": "poi_highlight", "title": "H", "type": "poi"},
            ]
        open(base + ".info.json", "w", encoding="utf-8").write(json.dumps(raw))
    return fake


def test_fetch_stores_sponsorblock_segments_apart_from_chapters(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(fetch.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    calls = []
    monkeypatch.setattr(common, "run", fake_run_sponsor(calls))
    info = common.load_json(fetch.fetch(URL) / "info.json")
    ytdlp = calls[0]
    assert ytdlp[ytdlp.index("--sponsorblock-mark") + 1] == "sponsor,selfpromo,interaction"
    assert info["skip"] == [{"s": 0.0, "e": 5.48, "kind": "sponsor"}, {"s": 1027.3, "e": 1145.0, "kind": "selfpromo"}]
    assert info["chapters"] == [{"start_time": 0, "end_time": 62, "title": "Intro"}]


def test_fetch_continues_without_sponsorblock_when_api_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    monkeypatch.setattr(fetch.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    calls = []
    monkeypatch.setattr(common, "run", fake_run_sponsor(calls, fail_sponsorblock=True))
    job = fetch.fetch(URL)
    assert "--sponsorblock-mark" in calls[0] and "--sponsorblock-mark" not in calls[1]
    assert common.load_json(job / "info.json")["skip"] == []
    assert common.read_status(job)["steps"]["fetch"]["ok"] is True


@pytest.mark.network
@pytest.mark.slow
def test_real_sponsorblock_segments(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    info = common.load_json(fetch.fetch("https://www.youtube.com/watch?v=pTn6Ewhb27k") / "info.json")
    assert any(s["kind"] == "sponsor" and s["s"] > 1000 for s in info["skip"])
    assert all("start_time" in c for c in info["chapters"])
    none = common.load_json(fetch.fetch("https://www.youtube.com/watch?v=fwiEcPCXLcI") / "info.json")
    assert none["skip"] == []
