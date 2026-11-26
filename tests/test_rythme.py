import subprocess
import wave

import pytest

from ideo import common, rythme, timeline, transcribe


def make_video(path, seconds, color):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c={color}:s=64x64:d={seconds}",
                    "-pix_fmt", "yuv420p", str(path)], check=True)


def make_video_with_audio(path, seconds):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=black:s=64x64:d={seconds}",
                    "-f", "lavfi", "-i", f"anullsrc=r=16000:cl=mono:d={seconds}",
                    "-pix_fmt", "yuv420p", "-shortest", str(path)], check=True)


def concat_videos(parts, out_path, tmp_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    listing = tmp_path / "concat.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-pix_fmt", "yuv420p", str(out_path)], check=True)


def write_tone_wav(path, seconds, rate=16000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(2 * int(rate * seconds)))


def test_plans_from_timeline_converts_frames_to_seconds():
    tl = {"fps": 30, "segments": [{"from": 0, "to": 30}, {"from": 30, "to": 90}]}
    assert rythme.plans_from_timeline(tl) == [(0.0, 1.0), (1.0, 3.0)]


def test_words_from_timeline_flattens_captions():
    tl = {"fps": 30, "captions": [{"words": [{"w": "Bonjour", "from": 0, "to": 15}, {"w": "monde", "from": 15, "to": 30}]}]}
    assert rythme.words_from_timeline(tl) == [{"w": "Bonjour", "s": 0.0, "e": 0.5}, {"w": "monde", "s": 0.5, "e": 1.0}]


def test_mesurer_computes_plan_and_word_rate():
    plans = [(0.0, 2.0), (2.0, 4.0)]
    words = [{"w": "un", "s": 0.1, "e": 0.3}, {"w": "deux", "s": 0.5, "e": 0.8}, {"w": "trois", "s": 2.2, "e": 2.5}]
    r = rythme.mesurer(plans, words)
    assert r.duree == 4.0
    assert r.n_plans == 2
    assert r.plans_par_min == 30.0
    assert r.plan_sec_moyen == 2.0
    assert r.n_mots == 3
    assert r.mots_par_sec == 0.75
    assert r.n_pauses == 1
    assert r.pauses_sec == 1.4
    assert r.mots_par_sec_parole == 3.0
    assert r.mots_par_plan_moyen == 1.5


def test_mesurer_handles_empty_input():
    r = rythme.mesurer([], [])
    assert r.duree == 0.0
    assert r.n_plans == 0
    assert r.plans_par_min == 0.0
    assert r.mots_par_sec == 0.0


def test_depuis_job_reads_real_timeline(job_with_offsets):
    job = job_with_offsets
    path = timeline.build_timeline(job, 1, 1)
    attendu = len(common.load_json(path)["segments"])
    mesures = rythme.depuis_job(job)
    assert set(mesures) == {1}
    r = mesures[1]
    assert r.n_plans == attendu
    assert r.n_mots > 0
    assert r.duree > 0


def test_depuis_job_sans_timeline_leve_une_erreur(job_with_fixtures):
    with pytest.raises(common.IdeoError):
        rythme.depuis_job(job_with_fixtures)


def test_plans_from_video_detects_a_scene_cut(tmp_path):
    first, second = tmp_path / "noir.mp4", tmp_path / "blanc.mp4"
    make_video(first, 1, "black")
    make_video(second, 1, "white")
    video = tmp_path / "scene.mp4"
    concat_videos([first, second], video, tmp_path)
    plans = rythme.plans_from_video(video, seuil=0.3)
    assert len(plans) == 2
    assert plans[0][1] == pytest.approx(1.0, abs=0.1)
    assert plans[-1][1] == pytest.approx(2.0, abs=0.2)


def test_plans_from_video_merges_a_flash_into_one_cut(tmp_path):
    parts = [tmp_path / "a.mp4", tmp_path / "flash.mp4", tmp_path / "b.mp4"]
    make_video(parts[0], 1, "black")
    make_video(parts[1], 0.1, "white")
    make_video(parts[2], 1, "red")
    video = tmp_path / "flash-cut.mp4"
    concat_videos(parts, video, tmp_path)
    assert len(rythme.plans_from_video(video)) == 2


def test_words_from_video_reuses_whisper(monkeypatch, tmp_path):
    video = tmp_path / "clip.mp4"
    make_video_with_audio(video, 1)
    calls = []

    def fake_whisper_words(pcm, model, language):
        calls.append((model, language, len(pcm)))
        return [{"w": "test", "s": 0.1, "e": 0.4}], "fr"

    monkeypatch.setattr(transcribe, "whisper_words", fake_whisper_words)
    words = rythme.words_from_video(video, model="small", language="fr")
    assert words == [{"w": "test", "s": 0.1, "e": 0.4}]
    assert calls and calls[0][0] == "small" and calls[0][1] == "fr"


def test_rapport_formats_in_french():
    r = rythme.Rythme(duree=10.0, n_plans=5, plans_par_min=30.0, plan_sec_moyen=2.0, plan_sec_median=2.0,
                       n_mots=30, mots_par_sec=3.0, mots_par_sec_parole=3.5, n_pauses=4, pauses_sec=1.5,
                       mots_par_plan_moyen=6.0, mots_par_plan_median=6.0)
    text = rythme.rapport(r, label="partie 1")
    assert "Rythme partie 1" in text
    assert "5 plans" in text
    assert "30 mots" in text
    assert "," in text
