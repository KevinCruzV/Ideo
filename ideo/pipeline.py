import hashlib
import json
import os
import shutil
import time
from pathlib import Path

from ideo import assemble, common, config, compact, fetch, plan_check, render, timeline, transcribe, voice

PREPARED_FILES = ("info.json", "words.json", "lang.txt", "sfx.json", "skip.json", "transcript_compact.md")
AUDIO_FILES = ("source.wav", "source.m4a")
PREPARE_STEPS = ("fetch", "transcribe", "transcript")
PART_STEPS = ("voice", "assemble", "timeline", "render")
ASSEMBLY_FILES = ("part.wav", "offsets.json", "timeline.json", "music.json")
VOICE_FILES = ("voice-info.json", "voice-quality.json", "voice-prosody.json", "voice-hook.json")
PART_FILES = ASSEMBLY_FILES + VOICE_FILES
RENDER_CODE = ("align", "assemble", "countries", "i18n", "music", "pacing", "photo", "render", "scene_schema", "sfx",
               "timeline", "transitions")
VOICE_CODE = ("align", "eleven", "fidelity", "hookvoice", "lexicon", "numbers", "pacing", "prosody", "textmatch", "voice")
REPO = Path(__file__).resolve().parent.parent
REDONE: set[int] = set()


def resolve_job(arg: str) -> Path:
    candidates = [Path(arg).expanduser(), common.JOBS / arg]
    match = common.VIDEO_ID.search(arg)
    if match:
        candidates.append(common.JOBS / match.group(1))
    for path in candidates:
        if path.is_dir():
            return path.resolve()
    raise common.IdeoError(f"job introuvable : {arg}. Lance d'abord prepare <url>.")


def progress(job: Path, line: str) -> None:
    common.progress(job, line)


def prepare(url: str) -> tuple[Path, dict]:
    job = common.job_dir(url).resolve()
    fetch.fetch(url)
    progress(job, "OK fetch : audio et métadonnées")
    words = transcribe.transcribe(job)
    progress(job, f"OK transcribe : {len(words)} mots")
    info = compact.prepare_transcript(job)
    refusal = voice.unsupported(info["lang"])
    if refusal:
        common.mark(job, "transcript", False, refusal)
        raise common.IdeoError(refusal)
    progress(job, f"OK transcript : {info['paragraphs']} paragraphes, {info['sfx']} sons")
    return job, info


def _steps(job: Path) -> dict:
    return common.read_status(job)["steps"]


def _ok(steps: dict, name: str) -> bool:
    return bool(steps.get(name, {}).get("ok"))


def prepared(job: Path) -> bool:
    steps = _steps(job)
    return all(_ok(steps, s) for s in PREPARE_STEPS) and (job / "transcript_compact.md").exists()


def voiced_scene(scene: dict) -> dict:
    if scene.get("type") == "quote":
        return scene
    return {k: v for k, v in scene.items() if k != "src"}


def _voice_settings(lang: str, job: Path | None = None) -> dict:
    chosen = config.engine(job)
    if chosen == "elevenlabs":
        return {"engine": "elevenlabs", "voice": config.eleven_voice_id(job), "model": config.eleven_model(job),
                **config.eleven_settings(job)}
    if lang in voice.KYUTAI_LANGS and chosen == "kyutai":
        settings = {"engine": "kyutai", "voice": config.kyutai_voice(), "padding": config.kyutai_padding_bonus()}
        hook = [config.kyutai_hook_temp(), config.kyutai_hook_padding_bonus()]
        if hook != [config.DEFAULT_HOOK_TEMP, config.DEFAULT_HOOK_PADDING]:
            settings["hook"] = hook
        return settings
    return {"engine": "edge", "voice": config.voice_for(lang), "rate": config.rate()}


def _fingerprint(files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(REPO).as_posix().encode("utf-8"))
        try:
            digest.update(path.read_bytes())
        except OSError:
            continue
    return digest.hexdigest()[:16]


def code_version() -> str:
    files = [REPO / "ideo" / f"{name}.py" for name in RENDER_CODE]
    files += [p for p in (REPO / "render" / "src").rglob("*") if p.is_file()]
    return _fingerprint(files)


def voice_code_version() -> str:
    return _fingerprint([REPO / "ideo" / f"{name}.py" for name in VOICE_CODE])


def voice_hash(plan: dict, job: Path | None = None) -> str:
    settings = _voice_settings(plan["lang"], job)
    content = {"lang": plan["lang"], "voice": settings}
    if settings["engine"] != "elevenlabs":
        content["code"] = voice_code_version()
    return hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def part_hash(plan: dict, part: dict, job: Path | None = None) -> str:
    content = {
        "lang": plan["lang"],
        "voice": voice_hash(plan, job),
        "code": code_version(),
        "total": len(plan["parts"]),
        "title": part["title"],
        "segments": voice.segments(plan, part),
        "scenes": [voiced_scene(scene) for scene in part["scenes"]],
    }
    raw = json.dumps(content, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _part_dir(job: Path, n: int) -> Path:
    return job / "parts" / f"{n:02d}"


def _stored_hash(job: Path, n: int) -> str | None:
    path = _part_dir(job, n) / "plan.hash"
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def _unmark(job: Path, names: list[str]) -> None:
    status = common.read_status(job)
    for name in names:
        status["steps"].pop(name, None)
    common.save_json(job / "status.json", status)


def _stored_voice_hash(job: Path, n: int) -> str | None:
    path = _part_dir(job, n) / "voice.hash"
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def keeps_voice(job: Path, plan: dict, n: int) -> bool:
    stored = _stored_voice_hash(job, n)
    if stored is not None:
        return stored == voice_hash(plan, job)
    info = voice.read_info(_part_dir(job, n))
    return info.get("engine") == "elevenlabs" and _voice_settings(plan["lang"], job)["engine"] == "elevenlabs"


def invalidate(job: Path, n: int, keep_voice: bool = False, wanted: list[str] | None = None) -> None:
    part_dir = _part_dir(job, n)
    for path in [part_dir / name for name in ASSEMBLY_FILES]:
        path.unlink(missing_ok=True)
    if keep_voice:
        names = set(wanted or [])
        for path in part_dir.glob("seg_*"):
            if path.name.split(".")[0] not in names:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink(missing_ok=True)
    else:
        for path in list(part_dir.glob("seg_*")) + [part_dir / name for name in VOICE_FILES]:
            path.unlink(missing_ok=True)
    out = job / "out"
    for name in (f"partie-{n:02d}.mp4", f"description-{n:02d}.txt"):
        (out / name).unlink(missing_ok=True)
    if n == 1:
        (out / "video.mp4").unlink(missing_ok=True)
        (out / "description.txt").unlink(missing_ok=True)
    _unmark(job, [f"{step}-{n:02d}" for step in PART_STEPS])


def rendered_at(job: Path, plan: dict, n: int) -> float | None:
    path = render.mp4_path(job, plan, n)
    return path.stat().st_mtime if path.exists() else None


def _when(stamp: float, today: str, other: str) -> str:
    moment = time.localtime(stamp)
    clock = time.strftime("%H:%M", moment)
    if time.strftime("%Y-%m-%d", moment) == time.strftime("%Y-%m-%d"):
        return f"{today} {clock}"
    return f"{other} {time.strftime('%d/%m', moment)} à {clock}"


def freshness(job: Path, only: int | None = None) -> str:
    job = Path(job)
    plan = common.load_json(job / "plan.json")
    numbers = [p["n"] for p in plan["parts"] if only is None or p["n"] == only]
    single = len(plan["parts"]) == 1
    redone = [n for n in numbers if n in REDONE]
    kept = [n for n in numbers if n not in REDONE]
    label = lambda n: "vidéo" if single else f"partie {n}"
    if not redone:
        stamps = [rendered_at(job, plan, n) for n in numbers]
        stamps = [s for s in stamps if s is not None]
        when = _when(min(stamps), "de", "du") if stamps else "d'une date inconnue"
        return f"Version : AUCUNE nouvelle vidéo, celle-ci date {when} (rien n'a changé depuis)"
    pieces = []
    for n in redone:
        stamp = rendered_at(job, plan, n)
        pieces.append(f"{label(n)} refaite {_when(stamp, 'à', 'le')}" if stamp else f"{label(n)} refaite")
    for n in kept:
        stamp = rendered_at(job, plan, n)
        pieces.append(f"{label(n)} inchangée" + (f" (rendue {_when(stamp, 'à', 'le')})" if stamp else ""))
    return "Version : " + ", ".join(pieces)


def _clean_extra_outputs(job: Path, plan: dict) -> None:
    numbers = {p["n"] for p in plan["parts"]}
    keep = {render.mp4_path(job, plan, n).name for n in numbers}
    keep |= {render.description_path(job, plan, n).name for n in numbers}
    keep |= {render.cover_path(job, plan, n).name for n in numbers}
    out = job / "out"
    if out.is_dir():
        for pattern in ("video.mp4", "partie-*.mp4", "description*.txt", "cover*.png"):
            for path in out.glob(pattern):
                if path.name not in keep:
                    path.unlink()
    parts = job / "parts"
    if parts.is_dir():
        for path in parts.iterdir():
            if path.is_dir() and not (path.name.isdigit() and int(path.name) in numbers):
                shutil.rmtree(path)


def _done(job: Path, plan: dict, n: int, digest: str) -> bool:
    return (_stored_hash(job, n) == digest and _ok(_steps(job), f"render-{n:02d}")
            and render.mp4_path(job, plan, n).exists())


def produce(job: Path, only: int | None = None, pay: bool = False) -> list[Path]:
    job = Path(job)
    config.lock_final_voice(job)
    errors = plan_check.check_plan(job)
    if errors:
        raise common.IdeoError(f"plan.json contient {len(errors)} erreur(s) : lance check et corrige-les avant produce.")
    plan = common.load_json(job / "plan.json")
    parts = plan["parts"]
    if only is not None and not any(p["n"] == only for p in parts):
        raise common.IdeoError(f"partie {only} introuvable dans plan.json")
    _clean_extra_outputs(job, plan)
    REDONE.clear()
    outputs = []
    for part in parts:
        n = part["n"]
        if only is not None and n != only:
            continue
        digest = part_hash(plan, part, job)
        if _done(job, plan, n, digest) and not voice.stale(job, n) and assemble.mix_current(job, n):
            progress(job, f"OK partie {n:02d} : déjà rendue, inchangée")
        else:
            if _stored_hash(job, n) != digest:
                keep = keeps_voice(job, plan, n)
                voice.guard_redo(job, n, pay, keep)
                invalidate(job, n, keep, voice.done_segments(job, plan, part))
                _part_dir(job, n).mkdir(parents=True, exist_ok=True)
                (_part_dir(job, n) / "plan.hash").write_text(digest, encoding="utf-8")
                (_part_dir(job, n) / "voice.hash").write_text(voice_hash(plan, job), encoding="utf-8")
            voice.voice_part(job, n, pay=pay)
            progress(job, f"OK voice-{n:02d}")
            assemble.assemble_part(job, n)
            progress(job, f"OK assemble-{n:02d}")
            timeline.build_timeline(job, n, len(parts))
            progress(job, f"OK timeline-{n:02d}")
            render.render_part(job, n)
            progress(job, f"OK render-{n:02d}")
            REDONE.add(n)
        render.write_description(job, n)
        cover = render.write_cover(job, n)
        progress(job, f"OK cover-{n:02d}")
        outputs += [render.mp4_path(job, plan, n), cover, render.description_path(job, plan, n)]
    outputs.append(render.write_sources(job))
    progress(job, "OK sources")
    return [p.resolve() for p in outputs]


def status(job: Path) -> str:
    job = Path(job)
    steps = _steps(job)
    failed = [f"{name} ({info.get('detail', '')})" for name, info in steps.items() if not info.get("ok")]
    note = f" ; dernier échec : {failed[-1]}" if failed else ""
    if not prepared(job):
        last = "fetch" if _ok(steps, "fetch") else "rien"
        return f"fait : {last} ; suivant : prepare <url>{note}"
    plan_path, md = job / "plan.json", job / "plan.md"
    if not plan_path.exists():
        return f"fait : prepare ; suivant : écris plan.json puis lance check{note}"
    if not md.exists() or md.stat().st_mtime < plan_path.stat().st_mtime:
        return f"fait : prepare ; suivant : check{note}"
    plan = common.load_json(plan_path)
    todo = [p["n"] for p in plan["parts"] if not _done(job, plan, p["n"], part_hash(plan, p, job))]
    if todo:
        return f"fait : check ; suivant : produce (partie {todo[0]}){note}"
    return f"fait : produce ; suivant : rien, tout est dans {(job / 'out').resolve()}{note}"


def _link(src: Path, dst: Path) -> None:
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def deepen(job: Path) -> Path:
    job = Path(job)
    if not prepared(job):
        raise common.IdeoError(f"{job.name} n'est pas préparé : lance d'abord prepare <url>.")
    base = job.name[:11]
    k = 2
    while (job.parent / f"{base}-{k}").exists():
        k += 1
    new = job.parent / f"{base}-{k}"
    new.mkdir()
    for name in PREPARED_FILES:
        if (job / name).exists():
            shutil.copy2(job / name, new / name)
    for name in AUDIO_FILES:
        if (job / name).exists():
            _link(job / name, new / name)
    steps = _steps(job)
    common.save_json(new / "status.json", {"steps": {s: steps[s] for s in PREPARE_STEPS}})
    return new.resolve()
