import re
import shutil
import subprocess
from pathlib import Path

from ideo import assemble, common, plan_check, prosody, render, target

SILENCE_SECONDS = 1.2
SILENCE_DB = -35
LUFS_TOLERANCE = 1.0
FIRST_ITEM_SECONDS = 0.5
IDLE_SECONDS = 6.0
VIDEO_TOLERANCE = 0.5
CLIP_WINDOW = 0.3
HARD_MAX = 300
FAITHFUL = 0.80
FLAT_SHARE = 0.25
BOUNDARY_SEGMENTS = ("seg_00_hook", "seg_99_outro")
LEADING = ("'", "’", "-")
WORD = re.compile(r"\w", re.UNICODE)


def _sec(value: float) -> str:
    return f"{value:.1f}".replace(".", ",") + " s"


def _probe(path: Path) -> float | None:
    probe = shutil.which("ffprobe")
    if not probe:
        return None
    try:
        out = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True).stdout.strip()
        return float(out)
    except (ValueError, OSError):
        return None


def _silences(wav: Path) -> list[tuple[float, float]]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return []
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", str(wav), "-af",
         f"silencedetect=noise={SILENCE_DB}dB:d={SILENCE_SECONDS}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", result.stderr)]
    ends = [(float(e), float(d)) for e, d in re.findall(r"silence_end: (-?[\d.]+) \| silence_duration: ([\d.]+)", result.stderr)]
    return [(s, e) for s, (e, _) in zip(starts, ends)]


def _clip_windows(offsets: list) -> list[tuple[float, float]]:
    return [(o["clip"]["start"] - CLIP_WINDOW, o["clip"]["end"] + CLIP_WINDOW) for o in offsets if o.get("clip")]


def _scene_alerts(where: str, timeline: dict, offsets: list) -> list[tuple[str, str]]:
    fps = timeline["fps"]
    alerts = []
    number = 0
    for index, seg in enumerate(timeline["segments"]):
        if seg["kind"] != "scene":
            continue
        number += 1
        props = seg.get("props") or {}
        items = seg.get("items") or []
        at = f"{where}, scène {number} (à {_sec(seg['from'] / fps)})"
        if items:
            delay = (items[0]["at"] - seg["from"]) / fps
            if delay > FIRST_ITEM_SECONDS and not (props.get("kicker") or props.get("picto")):
                alerts.append(("premier-element-tardif", f"{at} : le premier élément arrive {_sec(delay)} après le début, écran vide. "
                              "Ancre le premier item sur un mot du début de « say » ou ajoute un « kicker » ou un « picto »."))
        has_clip = index < len(offsets) and offsets[index].get("clip")
        if seg.get("type") == "quote" or has_clip:
            continue
        points = sorted([seg["from"], seg["to"]] + [i["at"] for i in items] + list(seg.get("beats") or []))
        gap = max(b - a for a, b in zip(points, points[1:])) / fps
        if gap > IDLE_SECONDS:
            alerts.append(("scene-figee", f"{at} : rien n'apparaît pendant {_sec(gap)}. "
                          "Ajoute des items ancrés sur des mots de « say » ou coupe la scène en deux."))
    return alerts


def _caption_alerts(where: str, timeline: dict) -> list[tuple[str, str]]:
    fps = timeline["fps"]
    alerts = []
    for group in timeline.get("captions", []):
        for word in group["words"]:
            text = word["w"]
            if text.startswith(LEADING) or not WORD.search(text):
                alerts.append(("sous-titre-mal-decoupe", f"{where}, à {_sec(word['from'] / fps)} : sous-titre « {text} » mal découpé (apostrophe, "
                              "trait d'union isolé ou sans lettre). Relance la voix de cette partie."))
    return alerts


def _pitch_scores(out_dir: Path) -> dict:
    path = out_dir / "voice-prosody.json"
    try:
        data = common.load_json(path) if path.exists() else {}
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, (int, float)) and not isinstance(v, bool)} if isinstance(data, dict) else {}


def _comma(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def _flattest(scores: dict) -> str:
    return ", ".join(f"{name} ({_comma(score)})" for name, score in sorted(scores.items(), key=lambda p: p[1])[:3])


def _pitch_alerts(where: str, out_dir: Path) -> list[tuple[str, str]]:
    scores = _pitch_scores(out_dir)
    if not scores:
        return []
    flat = [n for n, s in scores.items() if s < prosody.FLAT]
    edges = [n for n in BOUNDARY_SEGMENTS if n in scores and scores[n] < prosody.FLAT]
    if len(flat) <= len(scores) * FLAT_SHARE and not edges:
        return []
    why = (f"{len(flat)} segments sur {len(scores)} sous {_comma(prosody.FLAT)}" if len(flat) > len(scores) * FLAT_SHARE
           else f"l'accroche ou la fin est plate ({', '.join(edges)})")
    return [("voix-plate", f"{where} : voix plate, {why}, score médian {_comma(prosody.median(list(scores.values())))}, "
                           f"les plus plats : {_flattest(scores)}. Relance la voix de cette partie ou reformule ces phrases.")]


def _part_alerts(job: Path, plan: dict, n: int) -> list[tuple[str, str]]:
    where = f"Partie {n}"
    out_dir = job / "parts" / f"{n:02d}"
    timeline_path, wav, offsets_path = out_dir / "timeline.json", out_dir / "part.wav", out_dir / "offsets.json"
    if not (timeline_path.exists() and wav.exists()):
        return [("timeline-absente", f"{where} : timeline ou audio absent. Relance produce pour cette partie.")]
    timeline = common.load_json(timeline_path)
    offsets = common.load_json(offsets_path) if offsets_path.exists() else []
    alerts = []
    windows = _clip_windows(offsets)
    for start, end in _silences(wav):
        if not any(start < b and end > a for a, b in windows):
            alerts.append(("silence-long", f"{where}, à {_sec(start)} : silence de {_sec(end - start)} dans la voix. "
                          "Raccourcis le texte autour ou relance la voix de cette partie."))
    loudness = assemble._integrated(wav)
    if loudness is not None and abs(loudness - assemble.TARGET_LUFS) > LUFS_TOLERANCE:
        alerts.append(("volume", f"{where} : volume {f"{loudness:.1f}".replace(".", ",")} LUFS, la cible est {assemble.TARGET_LUFS:.0f} LUFS. "
                      "Relance l'assemblage audio."))
    quality = out_dir / "voice-quality.json"
    scores = common.load_json(quality) if quality.exists() else {}
    for name, score in sorted(scores.items()) if isinstance(scores, dict) else []:
        if isinstance(score, (int, float)) and score < FAITHFUL:
            alerts.append(("voix-infidele", f"{where}, segment {name} : la voix s'écarte du texte (ressemblance "
                           f"{f'{score:.2f}'.replace('.', ',')}). Relance la voix de cette partie ou reformule le texte."))
    alerts += _pitch_alerts(where, out_dir)
    alerts += _scene_alerts(where, timeline, offsets)
    alerts += _caption_alerts(where, timeline)
    total = timeline["durationInFrames"] / timeline["fps"]
    if len(plan["parts"]) == 1:
        info = plan_check.read_json(job, "info.json", {})
        duration = info.get("duration") if isinstance(info, dict) else None
        if isinstance(duration, (int, float)) and not isinstance(duration, bool) and duration > 0:
            _, ranges = plan_check.sponsor_ranges(job, info)
            low, _ = target.bounds(target.useful_seconds(float(duration), ranges))
            if total < low or total > HARD_MAX:
                alerts.append(("duree-hors-cible", f"{where} : durée finale {_sec(total)}, hors de la durée conseillée ({low} à {HARD_MAX} s). "
                              "Ajuste le nombre ou la longueur des scènes si l'histoire le demande."))
    video = render.mp4_path(job, plan, n)
    if not video.exists() or video.stat().st_size == 0:
        alerts.append(("video-absente", f"{where} : la vidéo {video.name} est absente ou vide. Relance produce."))
    else:
        length = _probe(video)
        if length is not None and abs(length - total) > VIDEO_TOLERANCE:
            alerts.append(("video-duree-differente", f"{where} : la vidéo dure {_sec(length)} au lieu de {_sec(total)}. Relance produce pour cette partie."))
    return alerts


def run_coded(job: Path, only: int | None = None) -> list[tuple[str, str]]:
    job = Path(job)
    plan = common.load_json(job / "plan.json")
    alerts = []
    for part in plan["parts"]:
        if only is None or part["n"] == only:
            alerts += _part_alerts(job, plan, part["n"])
    out = job / "out"
    out.mkdir(parents=True, exist_ok=True)
    body = [f"# Contrôle de {job.name}", ""]
    body += [f"- {a}" for _, a in alerts] or ["Aucune alerte."]
    pitch = []
    for part in plan["parts"]:
        if only is None or part["n"] == only:
            scores = _pitch_scores(job / "parts" / f"{part['n']:02d}")
            if scores:
                pitch.append(f"- Partie {part['n']} : score médian {_comma(prosody.median(list(scores.values())))}, "
                             f"les plus plats : {_flattest(scores)}")
    if pitch:
        body += ["", "## Intonation", ""] + pitch
    (out / "qc.md").write_text("\n".join(body) + "\n", encoding="utf-8")
    return alerts


def run(job: Path, only: int | None = None) -> list[str]:
    return [text for _, text in run_coded(job, only)]


def summary(job: Path, alerts: list[str]) -> str:
    if not alerts:
        return "Contrôle : 0 alerte"
    word = "alerte" if len(alerts) == 1 else "alertes"
    return f"Contrôle : {len(alerts)} {word}, voir {Path(job) / 'out' / 'qc.md'}"
