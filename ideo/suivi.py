import contextlib
import os
import re
import time
from pathlib import Path

from ideo import common

DEBUT = "DÉBUT "
EN_COURS = "en-cours.json"
RENDERED = re.compile(r"Rendered (\d+)/(\d+)")
ENCODED = re.compile(r"Encoded (\d+)/(\d+)")
TAIL_BYTES = 4000


def duree(seconds: float) -> str:
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds} s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} min {seconds:02d}"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes:02d}"


class Etape:
    def __init__(self, name: str):
        self.name = name
        self.detail = ""


@contextlib.contextmanager
def etape(job: Path, name: str):
    job = Path(job)
    step = Etape(name)
    start = time.time()
    common.progress(job, f"{DEBUT}{name}")
    common.save_json(job / "logs" / EN_COURS, {"step": name, "pid": os.getpid(), "start": start})
    try:
        yield step
    except BaseException as err:
        message = str(err) or type(err).__name__
        common.progress(job, f"ERREUR {name} : {message} ({duree(time.time() - start)})")
        raise
    else:
        detail = f" : {step.detail}" if step.detail else ""
        common.progress(job, f"OK {name}{detail} ({duree(time.time() - start)})")
    finally:
        (job / "logs" / EN_COURS).unlink(missing_ok=True)


def avancement_rendu(text: str) -> str | None:
    for pattern, label in ((ENCODED, "encodage"), (RENDERED, "images")):
        found = pattern.findall(text)
        if found:
            done, total = (int(v) for v in found[-1])
            percent = round(100 * done / total) if total else 0
            return f"{label} {done}/{total} ({percent} %)"
    return None


def _tail(path: Path) -> str:
    with path.open("rb") as f:
        f.seek(max(0, path.stat().st_size - TAIL_BYTES))
        return f.read().decode("utf-8", errors="replace").replace("\r", "\n")


def _last_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1][:120] if lines else ""


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def rapport(job: Path) -> str:
    logs = Path(job) / "logs"
    progress = logs / "progress.log"
    if not progress.exists():
        return "rien n'a encore été lancé"
    lines = progress.read_text(encoding="utf-8").splitlines()
    current = common.load_json(logs / EN_COURS) if (logs / EN_COURS).exists() else None
    if current is None:
        last = lines[-1].split(" ", 2)[-1] if lines else ""
        state = "arrêté sur une erreur" if last.startswith("ERREUR") else "terminé"
        return f"{state} : {last}"
    name = current["step"]
    now = time.time()
    since = duree(now - current["start"])
    step_log = logs / f"{name}.log"
    watched = [p for p in (step_log, progress) if p.exists()]
    activity = max(p.stat().st_mtime for p in watched)
    detail = ""
    if step_log.exists():
        text = _tail(step_log)
        detail = avancement_rendu(text) or _last_line(text)
    where = f", {detail}" if detail else ""
    head = f"en cours : {name} depuis {since}{where}"
    if not _alive(int(current.get("pid", 0))):
        return f"{head} ; le processus s'est arrêté sans message : relance la commande"
    silent = now - activity
    if silent > common.STALL_SECONDS:
        log = step_log if step_log.exists() else progress
        return f"{head} ; aucune activité depuis {duree(silent)}, probablement bloqué : voir {log}"
    return f"{head} ; dernière activité il y a {duree(silent)}"
