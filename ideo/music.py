import hashlib
import re
import subprocess
import wave
from pathlib import Path

import numpy as np

from ideo import common, config, history

RATE = 48000
EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")
FADE_IN = 1.5
FADE_OUT = 2.0
CROSSFADE = 2.0
SMOOTH = 0.3
PAUSE_RISE_DB = 6.0
CLIP_DROP_DB = 4.0
NONE = "aucune"
CALM_RATIO = 0.6
LIVELY_RATIO = 0.8
INTRO_SECONDS = 8
MAX_START_SHARE = 0.4
RECENT = 3


def tracks(folder: Path) -> list[Path]:
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS and not p.name.startswith(("_", ".")))


def choose(job_id: str, available: list[Path], recent: list[str]) -> Path | None:
    if not available:
        return None
    start = int(hashlib.sha256(job_id.encode("utf-8")).hexdigest()[:8], 16) % len(available)
    for k in range(len(available)):
        candidate = available[(start + k) % len(available)]
        if candidate.name not in recent:
            return candidate
    return available[start]


def decode(path: Path, work: Path, log: Path) -> np.ndarray:
    out = Path(work) / "music-decoded.wav"
    common.run(["ffmpeg", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", str(out)], log)
    with wave.open(str(out), "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    out.unlink(missing_ok=True)
    return data


def _seconds_rms(samples: np.ndarray) -> np.ndarray:
    count = len(samples) // RATE
    if count == 0:
        return np.array([float(np.sqrt(np.mean(samples ** 2))) if len(samples) else 0.0])
    return np.sqrt((samples[:count * RATE].reshape(count, RATE) ** 2).mean(axis=1))


def start_offset(samples: np.ndarray) -> float:
    rms = _seconds_rms(samples)
    if len(rms) < INTRO_SECONDS * 2:
        return 0.0
    typical = float(np.median(rms))
    if typical <= 0 or float(rms[:INTRO_SECONDS].mean()) >= CALM_RATIO * typical:
        return 0.0
    limit = int(len(rms) * MAX_START_SHARE)
    for second in range(limit):
        if float(rms[second:second + 4].mean()) >= LIVELY_RATIO * typical:
            return float(second)
    return 0.0


def bed(samples: np.ndarray, offset: float, length: int) -> np.ndarray:
    begin = int(offset * RATE)
    piece = samples[begin:] if begin < len(samples) else samples
    if len(piece) == 0:
        return np.zeros(length, dtype=np.float32)
    cross = min(int(CROSSFADE * RATE), len(piece) // 2)
    out = piece.copy()
    while len(out) < length:
        if cross > 0:
            fade = np.linspace(0.0, 1.0, cross, dtype=np.float32)
            head = out[-cross:] * np.sqrt(1 - fade) + piece[:cross] * np.sqrt(fade)
            out = np.concatenate([out[:-cross], head, piece[cross:]])
        else:
            out = np.concatenate([out, piece])
    return out[:length].astype(np.float32)


def fades(length: int) -> np.ndarray:
    gain = np.ones(length, dtype=np.float32)
    fade_in, fade_out = min(int(FADE_IN * RATE), length), min(int(FADE_OUT * RATE), length)
    gain[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)
    gain[length - fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)
    return gain


def envelope(length: int, voice: list[tuple[float, float]], clips: list[tuple[float, float]]) -> np.ndarray:
    db = np.full(length, PAUSE_RISE_DB, dtype=np.float32)
    for start, end in voice:
        db[int(start * RATE):int(end * RATE)] = 0.0
    for start, end in clips:
        db[int(start * RATE):int(end * RATE)] = -CLIP_DROP_DB
    linear = 10 ** (db / 20)
    window = max(int(SMOOTH * RATE), 1)
    padded = np.pad(linear, (window // 2, window - window // 2 - 1), mode="edge")
    csum = np.cumsum(np.insert(padded, 0, 0.0))
    return ((csum[window:] - csum[:-window]) / window).astype(np.float32)


def write_wav(path: Path, samples: np.ndarray) -> None:
    clipped = np.clip(samples, -1.0, 1.0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((clipped * 32767).astype("<i2").tobytes())


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0


def choice_path(job: Path) -> Path:
    return Path(job) / "music.json"


def read_choice(job: Path) -> dict | None:
    path = choice_path(job)
    try:
        data = common.load_json(path) if path.exists() else None
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and isinstance(data.get("choice"), str) else None


def write_choice(job: Path, choice: str, path: str | None = None) -> None:
    common.save_json(choice_path(job), {"choice": choice, **({"path": path} if path else {})})


def resolve(choice: str, folder: Path) -> Path | None:
    candidate = Path(choice).expanduser()
    if candidate.is_absolute() or "/" in choice:
        return candidate if candidate.is_file() else None
    wanted = choice.strip().lower()
    for track in tracks(folder):
        if wanted in (track.stem.lower(), track.name.lower()):
            return track
    return None


def duration(path: Path) -> float | None:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True).stdout.strip()
        return float(out)
    except (ValueError, OSError):
        return None


def listing() -> list[str]:
    out = []
    for track in tracks(config.music_dir()):
        seconds = duration(track)
        stamp = f"{int(seconds) // 60}:{int(seconds) % 60:02d}" if seconds else "durée inconnue"
        out.append(f"{track.stem} ({stamp})")
    return out


def choose_for(job: Path, text: str) -> str:
    text = text.strip()
    if not text:
        raise common.IdeoError("dis quelle musique tu veux : « aucune », le nom d'un morceau de la liste ou un chemin de fichier.")
    if text.lower() == NONE:
        write_choice(job, NONE)
        return text
    target = resolve(text, config.music_dir())
    if target is None:
        names = ", ".join(t.stem for t in tracks(config.music_dir())) or "aucun morceau dans " + str(config.music_dir())
        raise common.IdeoError(f"morceau introuvable : {text}. Morceaux disponibles : {names}. "
                               "Donne un de ces noms, un chemin de fichier audio ou « aucune ».")
    if target.parent == config.music_dir():
        write_choice(job, target.stem)
    else:
        write_choice(job, target.name, str(target.resolve()))
    return text


def selected(job: Path) -> tuple[str, Path | None]:
    choice = read_choice(job)
    if choice:
        if choice["choice"].strip().lower() == NONE:
            return "none", None
        target = Path(choice["path"]) if choice.get("path") else resolve(choice["choice"], config.music_dir())
        return "choice", target if target and target.is_file() else None
    return ("auto", None) if config.music_enabled() else ("none", None)


def signature(job: Path | None = None) -> dict:
    mode, target = selected(job) if job else ("auto" if config.music_enabled() else "none", None)
    choice = read_choice(job) if job else None
    return {"mode": mode, "choice": choice["choice"] if choice else None, "level": config.music_level_db(),
            "folder": str(config.music_dir()), "sfx": config.transition_sfx_enabled(), "sfx_db": config.transition_sfx_db(),
            "has_tracks": bool(tracks(config.music_dir())) if mode == "auto" else bool(target)}


def title_of(track: Path) -> str:
    words = re.sub(r"[-_]+", " ", track.stem).strip()
    return words[:1].upper() + words[1:]


def attribution(folder: Path, track_name: str) -> str:
    licence = Path(folder) / "LICENCE.txt"
    title = title_of(Path(track_name))
    try:
        text = licence.read_text(encoding="utf-8")
    except OSError:
        return f"Musique : {Path(track_name).name}"
    author = re.search(r"\bpar ([A-Z][\w'’-]*(?: [A-Z][\w'’-]*)?)", text)
    if author and re.search(r"CC0|domaine public", text, re.IGNORECASE):
        return f"Musique : {title}, par {author.group(1)}, domaine public (CC0)"
    return f"Musique : {Path(track_name).name}"


def mix(raw: Path, offsets: list[dict], job: Path, out_dir: Path, work: Path, log: Path, loudness) -> dict:
    job = Path(job)
    sig = signature(job)
    info = {"signature": sig, "track": None}
    mode, target = selected(job)
    if mode == "none":
        return info
    if mode == "choice":
        if target is None:
            info["missing"] = True
            return info
        track = target
    else:
        available = tracks(config.music_dir())
        if not available:
            info["missing"] = True
            return info
        previous = _stored(out_dir)
        recent = history.recent_music(job.name, RECENT)
        track = next((t for t in available if previous and t.name == previous), None) or choose(job.name, available, recent)
    samples = decode(track, work, log)
    voice = read_wav(raw)
    length = len(voice)
    offset = start_offset(samples)
    music = bed(samples, offset, length)
    voice_lufs = loudness(raw)
    probe = work / "music-probe.wav"
    write_wav(probe, music)
    music_lufs = loudness(probe)
    base = (voice_lufs + config.music_level_db() - music_lufs) if voice_lufs is not None and music_lufs is not None else -30.0
    spans = [(o["start"], o["end"]) for o in offsets]
    clips = [(o["clip"]["start"], o["clip"]["end"]) for o in offsets if o.get("clip")]
    gain = envelope(length, spans, clips) * fades(length) * (10 ** (base / 20))
    stem = music * gain
    mixed = voice + stem
    peak = float(np.max(np.abs(mixed))) if len(mixed) else 0.0
    if peak > 0.98:
        mixed = mixed * (0.98 / peak)
    under = np.concatenate([stem[int(s * RATE):int(e * RATE)] for s, e in spans if int(e * RATE) > int(s * RATE)]) if spans else stem
    write_wav(probe, under)
    under_lufs = loudness(probe)
    probe.unlink(missing_ok=True)
    write_wav(raw, mixed)
    info.update({"track": track.name, "folder": str(track.parent), "offset": offset, "gain_db": round(base, 2),
                 "voice_lufs": voice_lufs, "music_under_voice_lufs": under_lufs})
    history.set_music(job.name, track.name)
    return info


def _stored(out_dir: Path) -> str | None:
    path = Path(out_dir) / "music.json"
    try:
        data = common.load_json(path) if path.exists() else {}
    except (OSError, ValueError):
        return None
    return data.get("track") if isinstance(data, dict) else None
