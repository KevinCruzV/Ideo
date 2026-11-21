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


def duration_alerts(job):
    return [t for c, t in qc.run_coded(job) if c == "duree-hors-cible"]


def test_under_the_hard_minimum_is_an_alert(made):
    job, _ = made
    found = duration_alerts(job)
    assert len(found) == 1 and "hors des bornes d'une vidéo (45 à 300 s)" in found[0] and "minimum de 45 s" in found[0]


def test_between_45_and_300_seconds_is_never_an_alert_even_under_the_advised_minimum(made):
    job, _ = made
    common.save_json(job / "info.json", {"duration": 1800})
    edit_timeline(job, lambda tl: tl.update(durationInFrames=60 * 30))
    assert duration_alerts(job) == []
    edit_timeline(job, lambda tl: tl.update(durationInFrames=45 * 30))
    assert duration_alerts(job) == []


def test_over_300_seconds_is_an_alert(made):
    job, _ = made
    edit_timeline(job, lambda tl: tl.update(durationInFrames=301 * 30))
    found = duration_alerts(job)
    assert len(found) == 1 and "Coupe des scènes" in found[0]


def test_the_lesson_never_asks_to_lengthen():
    from ideo import codes

    lesson = codes.LESSONS["duree-hors-cible"].lower()
    assert "300 s" in lesson and "allonge" not in lesson and "ajoute" not in lesson and "45" not in lesson


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
    monkeypatch.setattr(qc, "run_coded", lambda job, only=None: (_ for _ in ()).throw(RuntimeError("boum")))
    assert cli.main(["produce", str(produce_job[0])]) == 0
    assert "Contrôle : indisponible" in capsys.readouterr().out


def test_alerts_carry_stable_codes(made):
    job, _ = made
    plan = common.load_json(job / "plan.json")
    render.mp4_path(job, plan, 1).unlink()

    def idle(tl):
        scene = tl["segments"][2]
        scene["to"] = scene["from"] + 300
        scene["items"] = [{"el": "values.0", "at": scene["from"] + 3}]
        tl["captions"][0]["words"][0]["w"] = "'x"

    edit_timeline(job, idle)
    pairs = qc.run_coded(job)
    codes = {c for c, _ in pairs}
    assert {"video-absente", "scene-figee", "sous-titre-mal-decoupe"} <= codes
    assert [t for _, t in pairs] == qc.run(job)
    assert all(c == c.lower() and " " not in c for c in codes)


def test_unfaithful_voice_alert(made):
    job, _ = made
    common.save_json(job / "parts" / "01" / "voice-quality.json", {"seg_01": 0.95, "seg_02": 0.7, "seg_03": 0.8})
    pairs = [(c, t) for c, t in qc.run_coded(job) if c == "voix-infidele"]
    assert len(pairs) == 1 and "seg_02" in pairs[0][1] and "0,70" in pairs[0][1] and pairs[0][1].startswith("Partie 1")


def test_no_voice_quality_file_means_no_voice_alert(made):
    job, _ = made
    assert not [c for c, _ in qc.run_coded(job) if c == "voix-infidele"]


def test_voice_alert_is_a_code_originated_defect():
    from ideo import codes

    assert "voix-infidele" in codes.CODE_ONLY


def test_deliberate_act_pause_is_not_a_silence_alert(made):
    job, _ = made
    assert not [c for c, _ in qc.run_coded(job) if c == "silence-long"]


def prosody_file(job, scores):
    common.save_json(job / "parts" / "01" / "voice-prosody.json", scores)


def plate_alerts(job):
    return [t for c, t in qc.run_coded(job) if c == "voix-plate"]


def lively(**over):
    base = {n: 2.6 for n in ("seg_00_hook", "seg_01", "seg_02", "seg_03", "seg_04", "seg_05", "seg_99_outro")}
    base.update(over)
    return base


def test_lively_voice_gives_no_alert(made):
    job, _ = made
    prosody_file(job, lively())
    assert plate_alerts(job) == []


def test_more_than_a_quarter_flat_gives_the_alert(made):
    job, _ = made
    prosody_file(job, lively(seg_01=1.5, seg_02=1.6))
    found = plate_alerts(job)
    assert len(found) == 1 and found[0].startswith("Partie 1 : voix plate")
    assert "2 segments sur 7" in found[0]


def test_exactly_a_quarter_is_tolerated(made):
    job, _ = made
    scores = {f"seg_{i:02d}": 2.5 for i in range(1, 9)}
    scores.update({"seg_00_hook": 2.5, "seg_01": 1.5, "seg_02": 1.5})
    prosody_file(job, scores)
    assert plate_alerts(job) == []


def test_flat_hook_or_outro_gives_the_alert_alone(made):
    job, _ = made
    for name in ("seg_00_hook", "seg_99_outro"):
        prosody_file(job, lively(**{name: 1.9}))
        found = plate_alerts(job)
        assert len(found) == 1 and "accroche" in found[0] + " accroche" and name in found[0]
    prosody_file(job, lively(seg_00_hook=2.2, seg_99_outro=2.2))
    assert plate_alerts(job) == []


def test_alert_gives_median_and_the_three_flattest(made):
    job, _ = made
    prosody_file(job, lively(seg_01=1.5, seg_02=1.6, seg_03=1.7, seg_04=1.9))
    text = plate_alerts(job)[0]
    assert "score médian" in text and "seg_01 (1,50)" in text and "seg_02 (1,60)" in text and "seg_03 (1,70)" in text
    assert "seg_04" not in text


def test_qc_md_always_reports_the_intonation_when_measured(made):
    job, _ = made
    prosody_file(job, lively(seg_02=1.9))
    qc.run(job)
    body = (job / "out" / "qc.md").read_text(encoding="utf-8")
    assert "## Intonation" in body and "Partie 1 : score médian 2,60" in body and "seg_02 (1,90)" in body


def test_no_measure_no_section_and_no_alert(made):
    job, _ = made
    qc.run(job)
    assert "## Intonation" not in (job / "out" / "qc.md").read_text(encoding="utf-8")
    assert plate_alerts(job) == []


def test_flat_voice_is_a_code_originated_defect():
    from ideo import codes

    assert "voix-plate" in codes.CODE_ONLY


def test_a_beat_breaks_a_long_still_period(made):
    job, _ = made

    def still(tl):
        scene = tl["segments"][2]
        scene["to"] = scene["from"] + 300
        scene["items"] = [{"el": "values.0", "at": scene["from"] + 3}]
        scene.pop("beats", None)

    edit_timeline(job, still)
    assert any("rien n'apparaît pendant" in a for a in qc.run(job))

    def with_beats(tl):
        scene = tl["segments"][2]
        scene["beats"] = [scene["from"] + 120, scene["from"] + 240]

    edit_timeline(job, with_beats)
    assert not any("rien n'apparaît pendant" in a for a in qc.run(job))


def test_beats_that_leave_six_seconds_still_alert(made):
    job, _ = made

    def sparse(tl):
        scene = tl["segments"][2]
        scene["to"] = scene["from"] + 400
        scene["items"] = [{"el": "values.0", "at": scene["from"] + 3}]
        scene["beats"] = [scene["from"] + 100]

    edit_timeline(job, sparse)
    found = [a for a in qc.run(job) if "rien n'apparaît pendant" in a]
    assert found and "10,0 s" in found[0] or "10" in found[0]


def test_imperfect_hook_alert(made):
    job, _ = made
    common.save_json(job / "parts" / "01" / "voice-hook.json", {"passed": False, "failed": ["formule trop longue"], "takes": 12})
    found = [t for c, t in qc.run_coded(job) if c == "accroche-imparfaite"]
    assert len(found) == 1 and "formule trop longue" in found[0] and found[0].startswith("Partie 1 : l'accroche reste imparfaite")
    common.save_json(job / "parts" / "01" / "voice-hook.json", {"passed": True, "failed": [], "takes": 12})
    assert not [c for c, _ in qc.run_coded(job) if c == "accroche-imparfaite"]
    (job / "parts" / "01" / "voice-hook.json").unlink()
    assert not [c for c, _ in qc.run_coded(job) if c == "accroche-imparfaite"]


def test_imperfect_hook_is_a_code_originated_defect():
    from ideo import codes

    assert "accroche-imparfaite" in codes.CODE_ONLY


def test_a_hook_chosen_by_hand_raises_no_alert(made):
    job, _ = made
    common.save_json(job / "parts" / "01" / "voice-hook.json",
                     {"passed": False, "failed": ["fin traînante"], "takes": 12, "chosen": "manuel : prise validée à l'oreille"})
    assert not [c for c, _ in qc.run_coded(job) if c == "accroche-imparfaite"]
