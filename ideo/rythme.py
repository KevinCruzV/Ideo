import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ideo import common, prosody, render, transcribe

SEUIL_SCENE = 0.15
FUSION = 0.4
PAUSE_MIN = 0.3
PTS_TIME = re.compile(r"pts_time:([\d.]+)")


@dataclass
class Rythme:
    duree: float
    n_plans: int
    plans_par_min: float
    plan_sec_moyen: float
    plan_sec_median: float | None
    n_mots: int
    mots_par_sec: float
    mots_par_sec_parole: float
    n_pauses: int
    pauses_sec: float
    mots_par_plan_moyen: float
    mots_par_plan_median: float | None


def plans_from_timeline(timeline: dict) -> list[tuple[float, float]]:
    fps = timeline["fps"]
    return [(seg["from"] / fps, seg["to"] / fps) for seg in timeline["segments"]]


def words_from_timeline(timeline: dict) -> list[dict]:
    fps = timeline["fps"]
    return [{"w": w["w"], "s": w["from"] / fps, "e": w["to"] / fps}
            for group in timeline.get("captions", []) for w in group["words"]]


def _ffmpeg() -> str:
    binary = shutil.which("ffmpeg")
    if not binary:
        raise common.IdeoError("ffmpeg est introuvable : installez-le (par exemple avec brew install ffmpeg).")
    return binary


def plans_from_video(video: Path, seuil: float = SEUIL_SCENE) -> list[tuple[float, float]]:
    video = Path(video)
    duree = render.probe_media(video)["duration"]
    result = subprocess.run(
        [_ffmpeg(), "-hide_banner", "-nostats", "-i", str(video), "-vf",
         f"select='gt(scene,{seuil})',showinfo", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    cuts: list[float] = []
    for t in sorted({float(t) for t in PTS_TIME.findall(result.stderr) if FUSION <= float(t) < duree - FUSION}):
        if not cuts or t - cuts[-1] >= FUSION:
            cuts.append(t)
    bornes = [0.0] + cuts + [duree]
    return list(zip(bornes, bornes[1:]))


def words_from_video(video: Path, model: str = "small", language: str | None = None) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        subprocess.run([_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
                        "-ac", "1", "-ar", "16000", "-f", "wav", str(wav)], check=True)
        pcm = transcribe.read_pcm(wav)
    words, _ = transcribe.whisper_words(pcm, model, language)
    return words


def _moyenne(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def mesurer(plans: list[tuple[float, float]], words: list[dict]) -> Rythme:
    fins = [e for _, e in plans] + [w["e"] for w in words]
    duree = max(fins) if fins else 0.0
    durees_plans = [e - s for s, e in plans]
    mots_par_plan = [sum(1 for w in words if s <= w["s"] < e) for s, e in plans]
    pauses = [b["s"] - a["e"] for a, b in zip(words, words[1:]) if b["s"] - a["e"] >= PAUSE_MIN]
    parole = words[-1]["e"] - words[0]["s"] - sum(pauses) if words else 0.0
    return Rythme(
        duree=round(duree, 2),
        n_plans=len(plans),
        plans_par_min=round(len(plans) / (duree / 60), 2) if duree else 0.0,
        plan_sec_moyen=_moyenne(durees_plans),
        plan_sec_median=prosody.median(durees_plans),
        n_mots=len(words),
        mots_par_sec=round(len(words) / duree, 2) if duree else 0.0,
        mots_par_sec_parole=round(len(words) / parole, 2) if parole > 0 else 0.0,
        n_pauses=len(pauses),
        pauses_sec=round(sum(pauses), 2),
        mots_par_plan_moyen=_moyenne(mots_par_plan),
        mots_par_plan_median=prosody.median(mots_par_plan),
    )


def depuis_job(job: Path) -> dict[int, Rythme]:
    job = Path(job)
    plan = common.load_json(job / "plan.json")
    out = {}
    for part in plan["parts"]:
        n = part["n"]
        path = job / "parts" / f"{n:02d}" / "timeline.json"
        if not path.exists():
            continue
        timeline = common.load_json(path)
        out[n] = mesurer(plans_from_timeline(timeline), words_from_timeline(timeline))
    if not out:
        raise common.IdeoError(f"aucune timeline trouvée pour {job.name} : lance produce d'abord.")
    return out


def depuis_video(video: Path, model: str = "small", language: str | None = None, seuil: float = SEUIL_SCENE) -> Rythme:
    video = Path(video)
    plans = plans_from_video(video, seuil)
    words = words_from_video(video, model, language)
    return mesurer(plans, words)


def _virgule(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def rapport(rythme: Rythme, label: str = "") -> str:
    titre = f"Rythme {label}".strip()
    return (
        f"{titre} : {_virgule(rythme.duree)} s, {rythme.n_plans} plans "
        f"({_virgule(rythme.plans_par_min)} plans/min, {_virgule(rythme.plan_sec_moyen)} s/plan en moyenne, "
        f"médiane {_virgule(rythme.plan_sec_median or 0.0)} s), {rythme.n_mots} mots "
        f"({_virgule(rythme.mots_par_sec)} mots/sec, {_virgule(rythme.mots_par_sec_parole)} hors pauses, "
        f"{rythme.n_pauses} pauses pour {_virgule(rythme.pauses_sec)} s, {_virgule(rythme.mots_par_plan_moyen)} mots/plan en moyenne, "
        f"médiane {_virgule(rythme.mots_par_plan_median or 0.0)} mots/plan)"
    )
