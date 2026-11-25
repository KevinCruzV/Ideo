import json
import shutil
import subprocess
from pathlib import Path

from ideo import common, i18n, photo, plan_check

REPO = Path(__file__).resolve().parent.parent
FPS = 30
WIDTH = 1080
HEIGHT = 1920
DURATION_TOLERANCE = 0.2
EXCERPT_WORDS = 8
COVER_FRAME = 59
PICTO_KEYS = ("picto", "left_picto", "right_picto")


def _plan(job: Path) -> dict:
    path = Path(job) / "plan.json"
    if not path.exists():
        raise common.IdeoError("plan.json est introuvable : écrivez d'abord le plan.")
    return common.load_json(path)


def _single(plan: dict) -> bool:
    return len(plan["parts"]) == 1


def mp4_path(job: Path, plan: dict, n: int) -> Path:
    name = "video.mp4" if _single(plan) else f"partie-{n:02d}.mp4"
    return Path(job) / "out" / name


def description_path(job: Path, plan: dict, n: int) -> Path:
    name = "description.txt" if _single(plan) else f"description-{n:02d}.txt"
    return Path(job) / "out" / name


def cover_path(job: Path, plan: dict, n: int) -> Path:
    name = "cover.png" if _single(plan) else f"cover-{n:02d}.png"
    return Path(job) / "out" / name


COVER_SCAN = 3


def _pictos_of(props: dict) -> list[str]:
    found = []
    for key in PICTO_KEYS:
        value = props.get(key)
        if isinstance(value, str) and value.strip():
            found.append(value.strip())
    for cell in props.get("cells") or []:
        if isinstance(cell, dict) and isinstance(cell.get("picto"), str) and cell["picto"].strip():
            found.append(cell["picto"].strip())
    return found


def cover_picto(part: dict) -> str | None:
    found = []
    for scene in part.get("scenes") or []:
        props = scene.get("props") if isinstance(scene, dict) else None
        if isinstance(props, dict):
            found.append(_pictos_of(props))
    for pictos in found[:COVER_SCAN]:
        for picto in pictos:
            if not picto.startswith("flag:"):
                return picto
    for pictos in found:
        if pictos:
            return pictos[0]
    return None


def cover_photo(job: Path, part: dict) -> str | None:
    stored = photo.all_stored(job)
    if not stored:
        return None
    for scene in part.get("scenes") or []:
        if not isinstance(scene, dict):
            continue
        props = scene.get("props")
        if scene.get("type") != "person-card" or not isinstance(props, dict) or props.get("photo") is not True:
            continue
        name = props.get("name")
        found = photo.match(stored, name) if isinstance(name, str) else None
        if found:
            return found["image"]
    return None


def cover_props(plan: dict, part: dict, job: Path | None = None) -> dict:
    lang = plan.get("lang") or "fr"
    props = {
        "title": part["title"],
        "hook": part.get("hook") or "",
        "picto": cover_picto(part),
        "watermark": common.WATERMARK,
        "part": part["n"],
        "total": len(plan["parts"]),
        "label": i18n.t("part_label", lang),
    }
    if plan.get("mood") == "dark":
        props["mood"] = "dark"
    if job is not None:
        picture = cover_photo(Path(job), part)
        if picture:
            props["photo"] = picture
    return props


def write_cover(job: Path, n: int) -> Path:
    job = Path(job)
    plan = _plan(job)
    part = next((p for p in plan["parts"] if p["n"] == n), None)
    if part is None:
        raise common.IdeoError(f"partie {n} introuvable dans plan.json")
    props = cover_props(plan, part, job)
    part_dir = job / "parts" / f"{n:02d}"
    part_dir.mkdir(parents=True, exist_ok=True)
    if props.get("photo"):
        shutil.copyfile(job / props["photo"], part_dir / props["photo"])
    props_path = part_dir / "cover.json"
    out = cover_path(job, plan, n)
    if out.exists() and props_path.exists() and common.load_json(props_path) == props:
        return out
    common.save_json(props_path, props)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    log = job / "logs" / f"cover-{n:02d}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    common.run(
        [_pnpm(), "--dir", str(REPO / "render"), "exec", "remotion", "still", "Cover", str(out.resolve()),
         f"--props={props_path.resolve()}", f"--public-dir={part_dir.resolve()}", f"--frame={COVER_FRAME}"],
        log,
    )
    if not out.exists():
        raise common.IdeoError(f"la couverture n'a pas été produite : voir {log}")
    return out


def _pnpm() -> str:
    path = shutil.which("pnpm")
    if not path:
        raise common.IdeoError("pnpm est introuvable : installez-le (par exemple avec brew install pnpm).")
    return path


def probe_media(path: Path) -> dict:
    binary = shutil.which("ffprobe")
    if not binary:
        raise common.IdeoError("ffprobe est introuvable : installez ffmpeg (par exemple avec brew install ffmpeg).")
    try:
        result = subprocess.run(
            [binary, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
            capture_output=True, text=True,
        )
        data = json.loads(result.stdout or "{}")
    except (OSError, ValueError) as err:
        raise common.IdeoError(f"{Path(path).name} est illisible : {err}") from err
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fps = 0.0
    if video:
        num, _, den = str(video.get("avg_frame_rate", "0/1")).partition("/")
        try:
            fps = float(num) / float(den or 1)
        except (ValueError, ZeroDivisionError):
            fps = 0.0
    try:
        duration = float(data.get("format", {}).get("duration"))
    except (TypeError, ValueError):
        duration = 0.0
    return {
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "fps": fps,
        "duration": duration,
        "video_codec": video.get("codec_name") if video else None,
        "has_audio": audio is not None,
    }


def verify_mp4(path: Path, frames: int) -> dict:
    probe = probe_media(path)
    name = Path(path).name
    if probe["video_codec"] is None:
        raise common.IdeoError(f"{name} ne contient pas de piste vidéo : le rendu a échoué.")
    if (probe["width"], probe["height"]) != (WIDTH, HEIGHT):
        raise common.IdeoError(
            f"{name} fait {probe['width']}x{probe['height']} au lieu de {WIDTH}x{HEIGHT} : le rendu est incorrect."
        )
    if not probe["has_audio"]:
        raise common.IdeoError(f"{name} ne contient pas de piste audio : le rendu est incorrect.")
    expected = frames / FPS
    if abs(probe["duration"] - expected) > DURATION_TOLERANCE:
        raise common.IdeoError(
            f"{name} dure {probe['duration']:.2f} s au lieu de {expected:.2f} s : le rendu est incorrect."
        )
    return probe


def render_part(job: Path, n: int) -> Path:
    job = Path(job)
    step = f"render-{n:02d}"
    try:
        return _render(job, n)
    except common.IdeoError as err:
        common.mark(job, step, False, str(err))
        raise
    except Exception as err:
        common.mark(job, step, False, str(err))
        raise common.IdeoError(f"le rendu a échoué : {err}") from err


def _render(job: Path, n: int) -> Path:
    plan = _plan(job)
    if not any(p["n"] == n for p in plan["parts"]):
        raise common.IdeoError(f"partie {n} introuvable dans plan.json")
    part_dir = job / "parts" / f"{n:02d}"
    timeline = part_dir / "timeline.json"
    if not timeline.exists():
        raise common.IdeoError(f"timeline.json est introuvable : construisez d'abord la timeline de la partie {n}.")
    if not (part_dir / "part.wav").exists():
        raise common.IdeoError(f"part.wav est introuvable : assemblez d'abord l'audio de la partie {n}.")
    out = mp4_path(job, plan, n)
    step = f"render-{n:02d}"
    if out.exists() and out.stat().st_mtime >= timeline.stat().st_mtime and common.read_status(job)["steps"].get(
        step, {}
    ).get("ok"):
        return out

    pnpm = _pnpm()
    frames = common.load_json(timeline)["durationInFrames"]
    out.parent.mkdir(parents=True, exist_ok=True)
    log = job / "logs" / f"render-{n:02d}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.unlink(missing_ok=True)
    out.unlink(missing_ok=True)
    common.run(
        [pnpm, "--dir", str(REPO / "render"), "exec", "remotion", "render", "Short", str(out.resolve()),
         f"--props={timeline.resolve()}", f"--public-dir={part_dir.resolve()}"],
        log,
    )
    if not out.exists():
        raise common.IdeoError(f"le rendu n'a produit aucun fichier : voir {log}")
    probe = verify_mp4(out, frames)
    if not plan_check.MIN_SECONDS <= probe["duration"] <= plan_check.MAX_SECONDS:
        common.progress(job, f"ATTENTION partie {n:02d} : durée réelle {probe['duration']:.1f} s, hors de "
                             f"{plan_check.MIN_SECONDS} à {plan_check.MAX_SECONDS} s")
    common.mark(job, step, True, f"{out.name}, {probe['duration']:.1f} s")
    return out


def _excerpt(say: str) -> str:
    words = say.split()
    text = " ".join(words[:EXCERPT_WORDS])
    return text + ("..." if len(words) > EXCERPT_WORDS else "")


def _music_credit(job: Path) -> str | None:
    from ideo import config, music

    for path in sorted((job / "parts").glob("*/music.json")):
        try:
            info = common.load_json(path)
        except (OSError, ValueError):
            continue
        if isinstance(info, dict) and info.get("track"):
            return music.attribution(Path(info.get("folder") or config.music_dir()), info["track"])
    return None


def write_sources(job: Path) -> Path:
    job = Path(job)
    plan = _plan(job)
    info = common.load_json(job / "info.json")
    video_id = info["id"]
    lines = ["# Sources", ""]
    for part in plan["parts"]:
        lines.append(f"## Partie {part['n']} : {part['title']}")
        lines.append("")
        for i, scene in enumerate(part["scenes"], start=1):
            seconds = int(common.parse_ts(scene["src"]))
            url = f"https://www.youtube.com/watch?v={video_id}&t={seconds}s"
            lines.append(f"- Scène {i} ({scene['type']}) : {_excerpt(scene['say'])} {url}")
        lines.append("")
    credit = _music_credit(job)
    if credit:
        lines += [credit, ""]
    for picture in photo.credit_lines(job):
        lines += [picture, ""]
    path = job / "out" / "sources.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_description(job: Path, n: int) -> str:
    job = Path(job)
    plan = _plan(job)
    part = next((p for p in plan["parts"] if p["n"] == n), None)
    if part is None:
        raise common.IdeoError(f"partie {n} introuvable dans plan.json")
    speakers = []
    for scene in part["scenes"]:
        props = scene.get("props") if isinstance(scene.get("props"), dict) else {}
        who = props.get("speaker")
        who = who.strip() if scene.get("type") == "quote" and isinstance(who, str) else ""
        if who and who not in speakers:
            speakers.append(who)
    text = f"{part['title']}\n"
    if speakers:
        text += "\n" + i18n.t("voices_line", plan.get("lang", "en"), names=", ".join(speakers)) + "\n"
    path = description_path(job, plan, n)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text
