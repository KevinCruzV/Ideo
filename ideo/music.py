import hashlib
import os
import re
import shutil
import time
import unicodedata
import urllib.parse
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
CHOSEN = "choisis"
CREDITS = "credits.json"
DOWNLOAD_SUFFIXES = (".mp3", ".wav", ".m4a", ".ogg")
DOWNLOAD_MINUTES = 30
MIN_GAP_DB = 28.0
GAP_WINDOW = 3.0
SPEECH_FLOOR_DB = -50.0
PIXABAY = "https://pixabay.com/music/search/"


def tracks(folder: Path) -> list[Path]:
    folder = Path(folder)
    if not folder.is_dir():
        return []
    def audio(directory: Path) -> list[Path]:
        if not directory.is_dir():
            return []
        return [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS and not p.name.startswith(("_", "."))]

    return sorted(audio(folder) + audio(folder / CHOSEN))


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


def _db(samples: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) else 0.0
    return 20 * np.log10(rms) if rms > 0 else -200.0


def min_gap(voice: np.ndarray, stem: np.ndarray, spans: list[tuple[float, float]]) -> float | None:
    step = int(GAP_WINDOW * RATE)
    gaps = []
    for start, end in spans:
        a, b = int(start * RATE), int(end * RATE)
        for k in range(a, b, step):
            window = slice(k, min(k + step, b))
            if window.stop - window.start < min(step // 2, RATE // 2) or (window.stop - window.start < step // 2 and k != a):
                continue
            speech = _db(voice[window])
            if speech > SPEECH_FLOOR_DB:
                gaps.append(speech - _db(stem[window]))
    return round(min(gaps), 2) if gaps else None


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
    if target.parent in (config.music_dir(), config.music_dir() / CHOSEN):
        write_choice(job, target.stem)
    else:
        write_choice(job, target.name, str(target.resolve()))
    return text


def downloads_dir() -> Path:
    return Path(os.environ.get("IDEO_DOWNLOADS") or Path.home() / "Downloads")


def simple_name(filename: str) -> str:
    stem = Path(filename).stem
    plain = "".join(c for c in unicodedata.normalize("NFKD", stem.lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-") or "morceau"


def take_latest(job: Path) -> tuple[str, float | None]:
    folder = downloads_dir()
    limit = time.time() - DOWNLOAD_MINUTES * 60
    recent = []
    if folder.is_dir():
        recent = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in DOWNLOAD_SUFFIXES and p.stat().st_mtime >= limit]
    if not recent:
        raise common.IdeoError(f"aucun fichier audio téléchargé depuis {DOWNLOAD_MINUTES} minutes dans Téléchargements. "
                               "Clique sur « Téléchargement gratuit » sur la page du morceau, puis relance.")
    latest = max(recent, key=lambda p: p.stat().st_mtime)
    target_dir = config.music_dir() / CHOSEN
    target_dir.mkdir(parents=True, exist_ok=True)
    name = simple_name(latest.name)
    destination = target_dir / f"{name}{latest.suffix.lower()}"
    k = 2
    while destination.exists() and destination.read_bytes() != latest.read_bytes():
        destination = target_dir / f"{name}-{k}{latest.suffix.lower()}"
        k += 1
    if not destination.exists():
        shutil.copy2(latest, destination)
    credits_path = target_dir / CREDITS
    try:
        credits = common.load_json(credits_path) if credits_path.exists() else {}
    except (OSError, ValueError):
        credits = {}
    credits.setdefault(destination.stem, {"original": latest.name})
    common.save_json(credits_path, credits)
    write_choice(job, destination.stem)
    return destination.stem, duration(destination)


def search_link(kind: str) -> str:
    text = kind.strip()
    if not text:
        raise common.IdeoError("dis quel type de musique chercher, par exemple « lofi chill ».")
    return PIXABAY + urllib.parse.quote(text, safe="") + "/"


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


def _credit(folder: Path, track_name: str) -> str | None:
    path = Path(folder) / CREDITS
    try:
        data = common.load_json(path) if path.exists() else {}
    except (OSError, ValueError):
        return None
    entry = data.get(Path(track_name).stem) if isinstance(data, dict) else None
    if not isinstance(entry, dict) or not entry.get("title"):
        return None
    parts = [entry["title"]] + [f"par {entry['artist']}"] * bool(entry.get("artist")) + [entry["source"]] * bool(entry.get("source"))
    return "Musique : " + ", ".join(parts)


def attribution(folder: Path, track_name: str) -> str:
    credit = _credit(folder, track_name)
    if credit:
        return credit
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
    gap = min_gap(voice, stem, spans)
    corrected = 0.0
    limit = min(MIN_GAP_DB, -config.music_level_db() - 2)
    if gap is not None and gap < limit:
        corrected = round(limit - gap, 2)
        stem = stem * (10 ** (-corrected / 20))
        gap = min_gap(voice, stem, spans)
    mixed = voice + stem
    peak = float(np.max(np.abs(mixed))) if len(mixed) else 0.0
    if peak > 0.98:
        mixed = mixed * (0.98 / peak)
    under = np.concatenate([stem[int(s * RATE):int(e * RATE)] for s, e in spans if int(e * RATE) > int(s * RATE)]) if spans else stem
    write_wav(probe, under)
    under_lufs = loudness(probe)
    probe.unlink(missing_ok=True)
    write_wav(raw, mixed)
    info.update({"track": track.name, "folder": str(track.parent), "offset": offset, "min_gap_db": gap,
                 "gap_corrected_db": corrected, "gain_db": round(base, 2),
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
