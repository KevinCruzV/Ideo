import subprocess

import pytest

from ideo import cli, common, qc, render, timeline
from tests.test_cli import produce_job


def make_video(path, seconds):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=black:s=64x64:d={seconds}",
                    "-pix_fmt", "yuv420p", str(path)], check=True)


@pytest.fixture
def made(job_with_offsets):
    job = job_with_offsets
    tl_path = timeline.build_timeline(job, 1, 1)
    tl = common.load_json(tl_path)
    plan = common.load_json(job / "plan.json")
    make_video(render.mp4_path(job, plan, 1), tl["durationInFrames"] / tl["fps"])
    return job, tl_path


def alerts_of(job):
    return qc.run(job)


def test_writes_qc_md_and_reports_no_alert_summary(made):
    job, _ = made
    alerts = qc.run(job)
    text = (job / "out" / "qc.md").read_text(encoding="utf-8")
    assert text.startswith("# Contrôle de ")
    assert (not alerts and "Aucune alerte." in text) or all(f"- {a}" in text for a in alerts)
    assert qc.summary(job, []) == "Contrôle : 0 alerte"
    assert qc.summary(job, ["a"]).startswith("Contrôle : 1 alerte, voir ")
    assert qc.summary(job, ["a", "b", "c"]).startswith("Contrôle : 3 alertes, voir ")


def edit_timeline(job, mutate):
    path = job / "parts" / "01" / "timeline.json"
    tl = common.load_json(path)
    mutate(tl)
    common.save_json(path, tl)


def test_missing_video_is_an_alert(made):
    job, _ = made
    plan = common.load_json(job / "plan.json")
    render.mp4_path(job, plan, 1).unlink()
    assert any("absente ou vide" in a and a.startswith("Partie 1") for a in qc.run(job))


def test_empty_video_is_an_alert(made):
    job, _ = made
    plan = common.load_json(job / "plan.json")
    render.mp4_path(job, plan, 1).write_bytes(b"")
    assert any("absente ou vide" in a for a in qc.run(job))


def test_video_duration_mismatch(made):
    job, _ = made
    plan = common.load_json(job / "plan.json")
    make_video(render.mp4_path(job, plan, 1), 3)
    assert any("la vidéo dure" in a for a in qc.run(job))


def test_first_item_too_late_without_kicker_or_picto(made):
    job, _ = made

    def late(tl):
        scene = tl["segments"][2]
        scene["items"][0]["at"] = scene["from"] + 20

    edit_timeline(job, late)
    found = [a for a in qc.run(job) if "premier élément" in a]
    assert found and found[0].startswith("Partie 1, scène 2 (à ")

    def excused(tl):
        tl["segments"][2]["props"]["kicker"] = "1991"

    edit_timeline(job, excused)
    assert not [a for a in qc.run(job) if "premier élément" in a]


def test_idle_scene_for_more_than_six_seconds(made):
    job, _ = made

    def idle(tl):
        scene = tl["segments"][2]
        scene["to"] = scene["from"] + 300
        scene["items"] = [{"el": "values.0", "at": scene["from"] + 3}]

    edit_timeline(job, idle)
    assert any("rien n'apparaît pendant" in a and "scène 2" in a for a in qc.run(job))


def test_bad_caption_words(made):
    job, _ = made

    def bad(tl):
        tl["captions"][0]["words"][0]["w"] = "'Union"
        tl["captions"][1]["words"][0]["w"] = "-"

    edit_timeline(job, bad)
    found = [a for a in qc.run(job) if "sous-titre" in a]
    assert any("« 'Union »" in a for a in found) and any("« - »" in a for a in found)


def test_loud_or_quiet_part(made, tmp_path):
    job, _ = made
    wav = job / "parts" / "01" / "part.wav"
    quiet = tmp_path / "quiet.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af", "volume=-9dB", str(quiet)], check=True)
    quiet.replace(wav)
    assert any("LUFS" in a for a in qc.run(job))


def test_long_silence_outside_source_clips(made):
    job, _ = made
    wav = job / "parts" / "01" / "part.wav"
    import numpy as np
    import wave

    with wave.open(str(wav), "rb") as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    pcm = np.concatenate([pcm[:48000], np.zeros(48000 * 2, dtype="<i2"), pcm[48000:]])
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(pcm.tobytes())
    assert any("silence de" in a for a in qc.run(job))


def test_duration_outside_advised_range(made):
    job, _ = made
    common.save_json(job / "info.json", {"duration": 1200})
    assert any("hors de la durée conseillée" in a for a in qc.run(job))


def test_missing_artifacts_are_an_alert_not_a_crash(job_with_fixtures):
    assert any("timeline ou audio absent" in a for a in qc.run(job_with_fixtures))


def test_cli_qc_prints_ok_line_then_alerts(made, capsys):
    job, _ = made
    plan = common.load_json(job / "plan.json")
    render.mp4_path(job, plan, 1).unlink()
    assert cli.main(["qc", str(job)]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out[0].startswith("OK qc : Contrôle : ") and out[1].startswith("ALERTE : Partie 1")


def test_produce_line_ends_with_the_control(produce_job, capsys):
    job = produce_job[0]
    assert cli.main(["produce", str(job)]) == 0
    line = capsys.readouterr().out.strip().splitlines()[0]
    assert line.startswith("OK produce : ") and " ; Contrôle : " in line


def test_qc_never_makes_produce_fail(produce_job, monkeypatch, capsys):
    monkeypatch.setattr(qc, "run", lambda job, only=None: (_ for _ in ()).throw(RuntimeError("boum")))
    assert cli.main(["produce", str(produce_job[0])]) == 0
    assert "Contrôle : indisponible" in capsys.readouterr().out
