import json
import math
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

from ideo import common, music, pacing, textmatch, transitions, voice

RATE = 48000
GAP_HOOK = 0.60
GAP_SCENE = 0.50
GAP_BREAK = 0.90
CLIP_PAD = 0.25
FADE = 0.08
QUOTE_WINDOW = 90.0
QUOTE_MARGIN = 0.15
TARGET_LUFS = -14.0
LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=11"
MEASURED = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")


def _measure(raw: Path) -> dict | None:
    result = subprocess.run(
        [_ffmpeg(), "-hide_banner", "-nostats", "-i", str(raw), "-af", LOUDNORM + ":print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    match = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", result.stderr)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        values = {k: float(data[k]) for k in MEASURED}
    except (ValueError, KeyError):
        return None
    return values if all(math.isfinite(v) for v in values.values()) else None


def _integrated(path: Path) -> float | None:
    result = subprocess.run(
        [_ffmpeg(), "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    found = re.findall(r"I:\s+(-?[\d.]+) LUFS", result.stderr)
    return float(found[-1]) if found else None


def reach_target(path: Path, work: Path, log: Path, tolerance: float = 0.2) -> None:
    loudness = _integrated(path)
    if loudness is None or abs(loudness - TARGET_LUFS) <= tolerance:
        return
    out = work / "gain.wav"
    gain = TARGET_LUFS - loudness
    common.run(
        [_ffmpeg(), "-y", "-i", str(path), "-af", f"volume={gain:.2f}dB,alimiter=limit=0.841:level=disabled",
         "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le", str(out)],
        log,
    )
    shutil.copyfile(out, path)


def _loudnorm_filter(raw: Path) -> str:
    values = _measure(raw)
    if values is None:
        return LOUDNORM
    return (f"{LOUDNORM}:measured_I={values['input_i']}:measured_TP={values['input_tp']}"
            f":measured_LRA={values['input_lra']}:measured_thresh={values['input_thresh']}"
            f":offset={values['target_offset']}:linear=true")


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


def _voice_pcm(out_dir: Path, name: str) -> bytes:
    pcm = _read_wav(out_dir / f"{name}.wav")
    words = out_dir / f"{name}.words.json"
    try:
        timed = common.load_json(words) if _gated(out_dir) and words.exists() else []
    except (OSError, ValueError):
        return pcm
    if not timed:
        return pcm
    gated = pacing.gate_breaths(np.frombuffer(pcm, dtype="<i2"), timed)
    return gated.astype("<i2").tobytes()


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


def _gated(out_dir: Path) -> bool:
    try:
        info = out_dir / "voice-info.json"
        return bool(info.exists() and common.load_json(info).get("engine") == "elevenlabs")
    except (OSError, ValueError, AttributeError):
        return False


def _music_current(job: Path, out_dir: Path) -> bool:
    path = out_dir / "music.json"
    try:
        stored = common.load_json(path) if path.exists() else None
    except (OSError, ValueError):
        return False
    return (isinstance(stored, dict) and stored.get("signature") == music.signature(job)
            and bool(stored.get("breath_gate", False)) == _gated(out_dir))


def mix_current(job: Path, n: int) -> bool:
    return _music_current(Path(job), Path(job) / "parts" / f"{n:02d}")


def _mix_music(raw: Path, offsets: list, job: Path, out_dir: Path, work: Path, log: Path) -> dict:
    rounded = [{"start": round(o["start"], 4), "end": round(o["end"], 4), "clip": o["clip"]} for o in offsets]
    try:
        info = music.mix(raw, rounded, job, out_dir, work, log, _integrated)
    except common.IdeoError:
        raise
    except Exception as err:
        info = {"signature": music.signature(job), "track": None, "error": str(err)}
    try:
        info["transitions"] = transitions.mix(raw, rounded)
    except Exception as err:
        info["transitions"] = {"enabled": False, "count": 0, "error": str(err)}
    return info


def _inputs(out_dir: Path, names: list[str], job: Path) -> list[Path]:
    paths = [out_dir / f"{name}.wav" for name in names] + [job / "plan.json", job / "sfx.json"]
    return [p for p in paths if p.exists()]


def _gap(names: list[str], index: int, scenes: dict, after_clip: bool) -> float:
    scene = scenes.get(names[index])
    if scene and scene.get("break") is True:
        return GAP_BREAK - CLIP_PAD if after_clip else GAP_BREAK
    if after_clip:
        return 0.0
    return GAP_HOOK if names[index - 1] == "seg_00_hook" else GAP_SCENE


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
    if out_wav.exists() and offsets_path.exists() and _music_current(job, out_dir):
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
            if index:
                gap = _gap(names, index, scenes, after_clip)
                if gap > 0:
                    chunks.append(_silence(gap))
                    cursor += gap
            pcm = _voice_pcm(out_dir, name)
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
        music_info = _mix_music(raw, offsets, job, out_dir, work, log)
        tmp_out = work / "part.wav"
        common.run(
            [_ffmpeg(), "-y", "-i", str(raw), "-af", _loudnorm_filter(raw), "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le",
             str(tmp_out)],
            log,
        )
        reach_target(tmp_out, work, log)
        shutil.copyfile(tmp_out, out_wav)

    for entry in offsets:
        entry["start"] = round(entry["start"], 4)
        entry["end"] = round(entry["end"], 4)
        if entry["clip"]:
            entry["clip"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in entry["clip"].items()}
    common.save_json(offsets_path, offsets)
    music_info["breath_gate"] = _gated(out_dir)
    common.save_json(out_dir / "music.json", music_info)
    common.mark(job, f"assemble-{n:02d}", True, f"{len(offsets)} segments, {offsets[-1]['end']:.1f} s")
    return out_wav
