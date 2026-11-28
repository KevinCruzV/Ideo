import functools
import math
import os
import random
import re
import struct
from pathlib import Path

import numpy as np

from ideo import common, music

ROOT = Path("/Library/Audio/Apple Loops")
PREFIX = "boucles"
SECONDS = 330
SECTION_BEATS = 32
BEATS = frozenset({4, 8, 16, 32})
HARMONY = frozenset({"Keyboards", "Guitars", "Strings", "Mallets", "Horn/Wind"})
SKIP = re.compile(r"\b(lead|fx|riser|swell|fill|topper|vox|vocals?|intro|outro|ending)\b", re.IGNORECASE)
STYLES = {
    "Funk": "funk", "Hip Hop": "hip-hop", "Electro House": "electro", "Electronic/Dance": "electro", "Dubstep": "dubstep",
    "Modern RnB": "rnb", "Chillwave": "chillwave", "Indie": "indie", "Rock/Blues": "blues", "Jazz": "jazz",
    "World/Ethnic": "monde",
}
LEVELS_DB = {"Drums": -21.0, "Bass": -22.0, "harmony": -25.0}
EDGE = 0.008
PEAK = 0.9
PATTERN = (
    ("drums", 0, "bass", 0, "harmony", 0),
    ("drums", 0, "bass", 0, "harmony", 0, "harmony", 1),
    ("drums", 1, "bass", 1, "harmony", 1),
    ("bass", 0, "harmony", 0, "harmony", 2),
)


def root() -> Path:
    folder = os.environ.get("IDEO_LOOPS")
    return Path(folder).expanduser() if folder else ROOT


def read(path: Path) -> dict | None:
    out = {}
    try:
        with open(path, "rb") as f:
            if f.read(8)[:4] != b"caff":
                return None
            while True:
                head = f.read(12)
                if len(head) < 12:
                    break
                kind, size = head[:4], struct.unpack(">q", head[4:])[0]
                if size < 0:
                    break
                if kind in (b"desc", b"pakt", b"uuid"):
                    body = f.read(size)
                    if kind == b"desc":
                        out["rate"] = struct.unpack(">d", body[:8])[0]
                    elif kind == b"pakt":
                        out["frames"] = struct.unpack(">q", body[8:16])[0]
                    elif b"category" in body:
                        parts = body[20:].split(b"\0")
                        for key, value in zip(parts[::2], parts[1::2]):
                            out[key.decode("utf-8", "replace")] = value.decode("utf-8", "replace")
                else:
                    f.seek(size, 1)
    except (OSError, struct.error):
        return None
    try:
        beats = int(out.get("beat count") or 0)
        seconds = out["frames"] / out["rate"]
    except (KeyError, ValueError, ZeroDivisionError):
        return None
    if beats not in BEATS or seconds <= 0 or out.get("time signature", "4/4") != "4/4":
        return None
    return {"path": str(path), "name": Path(path).stem, "style": STYLES.get(out.get("genre", "")),
            "category": out.get("category"), "key": out.get("key signature") or None,
            "tempo": round(beats / seconds * 60, 1), "beats": beats}


@functools.lru_cache(maxsize=4)
def _index(folder: str, stamp: float) -> tuple:
    base = Path(folder)
    if not base.is_dir():
        return ()
    loops = []
    for path in sorted(base.rglob("*.caf")):
        if SKIP.search(path.stem):
            continue
        loop = read(path)
        if loop and (loop["category"] == "Drums" or loop["category"] == "Bass" or loop["category"] in HARMONY):
            loops.append(loop)
    return tuple(loops)


def index() -> list[dict]:
    folder = root()
    try:
        stamp = folder.stat().st_mtime
    except OSError:
        return []
    return list(_index(str(folder), stamp))


def _role(loop: dict) -> str:
    return "harmony" if loop["category"] in HARMONY else loop["category"].lower()


def combos(loops: list[dict], style: str) -> list[dict]:
    pitched = {}
    for loop in loops:
        if loop["style"] == style and loop["category"] != "Drums" and loop["key"]:
            pitched.setdefault((loop["tempo"], loop["key"]), []).append(loop)
    out = []
    for (tempo, key), group in sorted(pitched.items()):
        bass = [l for l in group if l["category"] == "Bass"]
        harmony = [l for l in group if l["category"] in HARMONY]
        drums = [l for l in loops if l["category"] == "Drums" and l["tempo"] == tempo]
        own = [l for l in drums if l["style"] == style]
        if bass and harmony and drums:
            out.append({"tempo": tempo, "key": key, "bass": bass, "harmony": harmony, "drums": own or drums})
    return out


def styles(loops: list[dict] | None = None) -> list[str]:
    loops = index() if loops is None else loops
    return sorted(s for s in set(STYLES.values()) if combos(loops, s))


def pick(loops: list[dict], style: str, seed: str) -> dict:
    found = combos(loops, style)
    if not found:
        raise common.IdeoError(f"aucune boucle utilisable pour « {style} ». Styles possibles : {', '.join(styles(loops)) or 'aucun'}.")
    rng = random.Random(seed)
    combo = rng.choice(found)
    return {"tempo": combo["tempo"], "key": combo["key"],
            **{role: rng.sample(combo[role], min(count, len(combo[role]))) for role, count in (("drums", 2), ("bass", 2), ("harmony", 3))}}


def _level(samples: np.ndarray, db: float) -> np.ndarray:
    rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) else 0.0
    return samples * (10 ** (db / 20) / rms) if rms > 0 else samples


def _fit(samples: np.ndarray, length: int) -> np.ndarray:
    if len(samples) >= length:
        return samples[:length]
    return np.concatenate([samples, np.zeros(length - len(samples), dtype=np.float32)])


def _ramp(piece: np.ndarray, start: bool, end: bool) -> np.ndarray:
    edge = min(int(EDGE * music.RATE), len(piece) // 2)
    if edge <= 0:
        return piece
    piece = piece.copy()
    if start:
        piece[:edge] *= np.linspace(0.0, 1.0, edge, dtype=np.float32)
    if end:
        piece[-edge:] *= np.linspace(1.0, 0.0, edge, dtype=np.float32)
    return piece


def layers(choice: dict, sections: int) -> list[list[tuple[str, int]]]:
    out = []
    for i in range(sections):
        step = PATTERN[i % len(PATTERN)]
        chosen = []
        for role, n in zip(step[::2], step[1::2]):
            options = choice[role]
            if options:
                entry = (role, n % len(options))
                if entry not in chosen:
                    chosen.append(entry)
        out.append(chosen)
    return out


def compose(choice: dict, seconds: float, decode) -> np.ndarray:
    beat = 60.0 / choice["tempo"] * music.RATE
    section = SECTION_BEATS * beat
    count = max(1, math.ceil(seconds * music.RATE / section))
    total = int(round(count * section))
    out = np.zeros(total, dtype=np.float32)
    cache = {}
    plan = layers(choice, count)
    for i, chosen in enumerate(plan):
        begin = i * section
        for entry in chosen:
            role, n = entry
            loop = choice[role][n]
            span = loop["beats"] * beat
            if entry not in cache:
                level = LEVELS_DB["harmony" if role == "harmony" else loop["category"]]
                cache[entry] = _level(_fit(decode(Path(loop["path"])), int(round(span))), level).astype(np.float32)
            audio = cache[entry]
            reps = int(round(SECTION_BEATS / loop["beats"]))
            for k in range(reps):
                a = int(round(begin + k * span))
                b = min(int(round(begin + (k + 1) * span)), total)
                piece = _fit(audio, b - a)
                first = k == 0 and (i == 0 or entry not in plan[i - 1])
                last = k == reps - 1 and (i == count - 1 or entry not in plan[i + 1])
                out[a:b] += _ramp(piece, first, last)
    peak = float(np.max(np.abs(out))) if len(out) else 0.0
    return out * (PEAK / peak) if peak > 0 else out


def track_name(style: str) -> str:
    return f"music-{PREFIX}-{style}"


def make(job: Path, style: str, seconds: float = SECONDS) -> tuple[Path, dict]:
    job = Path(job)
    style = style.strip().lower()
    loops = index()
    if not loops:
        raise common.IdeoError(f"aucune boucle Apple Loops dans {root()} : ouvre GarageBand une fois pour les installer.")
    choice = pick(loops, style, f"{job.name}:{style}")
    log = job / "logs" / "boucles.log"

    def decode(path: Path) -> np.ndarray:
        return music.decode(path, job, log)

    samples = compose(choice, seconds, decode)
    target = job / f"{track_name(style)}.wav"
    music.write_wav(target, samples)
    credits_path = job / music.CREDITS
    try:
        credits = common.load_json(credits_path) if credits_path.exists() else {}
    except (OSError, ValueError):
        credits = {}
    credits[target.stem] = {"title": f"Composition Apple Loops ({style}, {choice['tempo']:g} bpm, {choice['key']})"}
    common.save_json(credits_path, credits)
    return target, choice


def describe(choice: dict) -> str:
    names = [l["name"] for role in ("drums", "bass", "harmony") for l in choice[role]]
    return f"{choice['tempo']:g} bpm, {choice['key']} : {', '.join(names)}"
