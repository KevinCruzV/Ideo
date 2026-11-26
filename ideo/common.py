import contextlib
import json
import math
import os
import re
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
VIDEO_ID = re.compile(r"(?:[?&]v=|youtu\.be/|/shorts/|/live/|/embed/)([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])")
ID = re.compile(r"[A-Za-z0-9_-]{11}")
YOUTUBE_HOSTS = frozenset({
    "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
    "youtu.be", "youtube-nocookie.com", "www.youtube-nocookie.com",
})
PATH_PREFIXES = ("shorts", "live", "embed")
WATERMARK = "@idevideos"
STALL_SECONDS = 600
POLL_SECONDS = 0.5


class IdeoError(Exception):
    pass


def _root() -> Path:
    return Path(os.environ.get("IDEO_HOME") or REPO_ROOT)


def __getattr__(name: str):
    if name == "ROOT":
        return _root()
    if name == "JOBS":
        return _root() / "jobs"
    raise AttributeError(name)


def _id_from(url: str) -> str | None:
    text = url.strip()
    if not text or text.startswith("-") or any(c.isspace() for c in text):
        return None
    if "://" not in text:
        text = "https://" + text
    try:
        parts = urlsplit(text)
        host = parts.hostname
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or host not in YOUTUBE_HOSTS or parts.username or parts.password:
        return None
    segments = [s for s in parts.path.split("/") if s]
    if host == "youtu.be":
        candidate = segments[0] if len(segments) == 1 else None
    elif segments == ["watch"]:
        values = parse_qs(parts.query).get("v", [])
        candidate = values[0] if len(values) == 1 else None
    elif len(segments) == 2 and segments[0] in PATH_PREFIXES:
        candidate = segments[1]
    else:
        candidate = None
    return candidate if candidate and ID.fullmatch(candidate) else None


def video_id(url: str) -> str:
    found = _id_from(url)
    if found is None:
        raise IdeoError(f"URL YouTube non reconnue : {url}. Donne un lien youtube.com ou youtu.be vers une vidéo.")
    return found


def canonical_url(url: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id(url)}"


def job_dir(url: str) -> Path:
    path = _root() / "jobs" / video_id(url)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(path, obj) -> None:
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_status(job: Path) -> dict:
    path = Path(job) / "status.json"
    if not path.exists():
        return {"steps": {}}
    return load_json(path)


def mark(job: Path, step: str, ok: bool, detail: str = "") -> None:
    status = read_status(job)
    status["steps"][step] = {
        "ok": ok,
        "detail": detail,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_json(Path(job) / "status.json", status)


def _stop(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()


def run(cmd: list[str], log: Path) -> None:
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    stalled = False
    try:
        with log.open("ab") as f:
            proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                    start_new_session=True, env={**os.environ, "PYTHONUNBUFFERED": "1"})
            size, quiet_since = log.stat().st_size, time.monotonic()
            while True:
                try:
                    code = proc.wait(timeout=POLL_SECONDS)
                    break
                except subprocess.TimeoutExpired:
                    pass
                now_size = log.stat().st_size
                if now_size != size:
                    size, quiet_since = now_size, time.monotonic()
                elif time.monotonic() - quiet_since > STALL_SECONDS:
                    stalled = True
                    _stop(proc)
                    code = proc.returncode
                    break
    except FileNotFoundError:
        raise IdeoError(f"Commande introuvable : {cmd[0]}") from None
    if stalled:
        minutes = max(1, round(STALL_SECONDS / 60))
        with log.open("a", encoding="utf-8") as f:
            f.write(f"\nideo : commande bloquée, arrêtée après {STALL_SECONDS} s sans aucune sortie\n")
        raise IdeoError(f"aucune activité depuis {minutes} min, commande arrêtée : {' '.join(str(c) for c in cmd[:3])}. Voir {log}")
    if code != 0:
        raise IdeoError(f"La commande a échoué (code {code}) : {' '.join(cmd)}. Voir {log}")


def parse_ts(s: str) -> float:
    total = 0.0
    for part in s.strip().split(":"):
        value = float(part)
        if not math.isfinite(value) or value < 0 or part.strip().startswith("-"):
            raise ValueError(f"minutage invalide : {s}")
        total = total * 60 + value
    return total


def progress(job: Path, line: str) -> None:
    log = Path(job) / "logs" / "progress.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log.open("a", encoding="utf-8") as f:
        f.write(f"{stamp} {line}\n")


def fmt_ts(sec: float) -> str:
    s = int(sec)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
