import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from ideo import common, textmatch, voice

RATE = 48000
SILENCE_GAP = 0.12
CLIP_PAD = 0.25
FADE = 0.08
QUOTE_WINDOW = 90.0
QUOTE_MARGIN = 0.15
LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=11"


def _ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise common.IdeoError("ffmpeg est introuvable : installez-le (par exemple avec brew install ffmpeg).")
    return path


def _read_wav(path: Path) -> bytes:
    try:
        with wave.open(str(path), "rb") as w:
            if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (RATE, 1, 2):
                raise common.IdeoError(f"{Path(path).name} doit être en 48 kHz mono 16 bits : relancez la voix.")
            return w.readframes(w.getnframes())
    except (wave.Error, EOFError) as err:
        raise common.IdeoError(f"{Path(path).name} est illisible : {err}") from err


def _silence(seconds: float) -> bytes:
    return bytes(2 * round(seconds * RATE))


def _seconds(pcm: bytes) -> float:
    return len(pcm) / 2 / RATE


def _source_audio(job: Path) -> Path:
    for name in ("source.m4a", "source.wav"):
        if (job / name).exists():
            return job / name
    raise common.IdeoError("l'audio source est introuvable (source.m4a ou source.wav) : relancez la récupération.")


def _source_duration(path: Path) -> float | None:
    probe = shutil.which("ffprobe")
    if not probe:
        return None
    try:
        out = subprocess.run(
            [probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True,
        ).stdout.strip()
        return float(out)
    except (ValueError, OSError):
        return None


def quote_bounds(words: list[dict], text: str, src: str, duration: float | None = None) -> tuple[float, float]:
    center = common.parse_ts(src)
    window = [w for w in words if abs(w["s"] - center) <= QUOTE_WINDOW]
    span = textmatch.find_span([w["w"] for w in window], text)
    if span is None:
        raise common.IdeoError(
            f"la citation « {text} » est introuvable dans la source autour de {src} (à {int(QUOTE_WINDOW)} s près)."
        )
    start = max(0.0, window[span[0]]["s"] - QUOTE_MARGIN)
    end = window[span[1]]["e"] + QUOTE_MARGIN
    if duration is not None:
        end = min(end, duration)
        start = min(start, end)
    return start, end


def sfx_bounds(sfx: list[dict], at: str) -> tuple[float, float]:
    target = common.parse_ts(at)
    for entry in sfx:
        if abs(common.parse_ts(entry["at"]) - target) < 1e-6:
            return float(entry["s"]), float(entry["e"])
    raise common.IdeoError(f"le son source repéré à {at} est introuvable dans sfx.json.")


def _cut(source: Path, start: float, end: float, work: Path, log: Path) -> bytes:
    length = max(end - start, 0.0)
    fade = min(FADE, length / 2)
    out = work / "clip.wav"
    chain = f"aresample={RATE},afade=t=in:st=0:d={fade:.3f},afade=t=out:st={length - fade:.3f}:d={fade:.3f}"
    common.run(
        [_ffmpeg(), "-y", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(source), "-vn", "-ac", "1",
         "-af", chain, "-ar", str(RATE), "-c:a", "pcm_s16le", str(out)],
        log,
    )
    pcm = _read_wav(out)
    out.unlink()
    return pcm


def _inputs(out_dir: Path, names: list[str], job: Path) -> list[Path]:
    paths = [out_dir / f"{name}.wav" for name in names] + [job / "plan.json", job / "sfx.json"]
    return [p for p in paths if p.exists()]


def assemble_part(job: Path, n: int) -> Path:
    job = Path(job)
    step = f"assemble-{n:02d}"
    try:
        return _assemble(job, n)
    except common.IdeoError as err:
        common.mark(job, step, False, str(err))
        raise
    except Exception as err:
        common.mark(job, step, False, str(err))
        raise common.IdeoError(f"l'assemblage audio a échoué : {err}") from err


def _assemble(job: Path, n: int) -> Path:
    plan = common.load_json(job / "plan.json")
    part = next((p for p in plan["parts"] if p["n"] == n), None)
    if part is None:
        raise common.IdeoError(f"partie {n} introuvable dans plan.json")
    out_dir = job / "parts" / f"{n:02d}"
    names = [name for name, _ in voice.segments(plan, part)]
    for name in names:
        if not (out_dir / f"{name}.wav").exists():
            raise common.IdeoError(f"{name}.wav est introuvable : lancez d'abord la voix de la partie {n}.")
    out_wav = out_dir / "part.wav"
    offsets_path = out_dir / "offsets.json"
    if out_wav.exists() and offsets_path.exists():
        newest = max(p.stat().st_mtime for p in _inputs(out_dir, names, job))
        if min(out_wav.stat().st_mtime, offsets_path.stat().st_mtime) >= newest:
            return out_wav

    scenes = {f"seg_{i:02d}": scene for i, scene in enumerate(part["scenes"], start=1)}
    words = common.load_json(job / "words.json") if (job / "words.json").exists() else []
    sfx = common.load_json(job / "sfx.json") if (job / "sfx.json").exists() else []
    log = job / "logs" / f"assemble-{n:02d}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.unlink(missing_ok=True)

    chunks: list[bytes] = []
    offsets = []
    cursor = 0.0
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        source = None
        source_len = None
        after_clip = False
        for index, name in enumerate(names):
            if index and not after_clip:
                chunks.append(_silence(SILENCE_GAP))
                cursor += SILENCE_GAP
            pcm = _read_wav(out_dir / f"{name}.wav")
            entry = {"seg": name, "start": cursor, "end": cursor + _seconds(pcm), "clip": None}
            chunks.append(pcm)
            cursor = entry["end"]
            scene = scenes.get(name)
            kind = None
            after_clip = False
            if scene and scene["type"] == "quote":
                kind = "quote"
            elif scene and scene.get("sfx"):
                kind = "sfx"
            if kind:
                after_clip = True
                if source is None:
                    source = _source_audio(job)
                    source_len = _source_duration(source)
                if kind == "quote":
                    s, e = quote_bounds(words, scene["props"]["text"], scene["src"], source_len)
                else:
                    s, e = sfx_bounds(sfx, scene["sfx"])
                clip = _cut(source, s, e, work, log)
                chunks.append(_silence(CLIP_PAD))
                cursor += CLIP_PAD
                clip_start = cursor
                chunks.append(clip)
                cursor += _seconds(clip)
                chunks.append(_silence(CLIP_PAD))
                cursor += CLIP_PAD
                entry["clip"] = {"start": clip_start, "end": clip_start + _seconds(clip), "kind": kind,
                                 "src_start": s, "src_end": e}
            offsets.append(entry)

        raw = work / "raw.wav"
        with wave.open(str(raw), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(b"".join(chunks))
        tmp_out = work / "part.wav"
        common.run(
            [_ffmpeg(), "-y", "-i", str(raw), "-af", LOUDNORM, "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le",
             str(tmp_out)],
            log,
        )
        shutil.copyfile(tmp_out, out_wav)

    for entry in offsets:
        entry["start"] = round(entry["start"], 4)
        entry["end"] = round(entry["end"], 4)
        if entry["clip"]:
            entry["clip"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in entry["clip"].items()}
    common.save_json(offsets_path, offsets)
    common.mark(job, f"assemble-{n:02d}", True, f"{len(offsets)} segments, {offsets[-1]['end']:.1f} s")
    return out_wav
