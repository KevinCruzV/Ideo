import shutil
import sys
from pathlib import Path

from ideo import common

INFO_FIELDS = ("id", "title", "channel", "webpage_url", "duration", "chapters", "language")

ERROR_PATTERNS = [
    (("private video",), "Impossible de récupérer cette vidéo privée."),
    (("confirm your age", "age-restricted", "age restricted"),
     "Cette vidéo a une restriction d'âge : impossible de la récupérer sans connexion."),
    (("live event", "is live", "premieres in", "will begin"),
     "Cette vidéo est en direct ou pas encore diffusée : réessayez une fois le direct terminé."),
    (("video unavailable", "not available", "removed", "been terminated"),
     "Cette vidéo est indisponible (supprimée, bloquée dans votre pays ou retirée)."),
]


def explain_ytdlp_error(stderr: str) -> str:
    low = stderr.lower()
    for needles, message in ERROR_PATTERNS:
        if any(n in low for n in needles):
            return message
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    last = lines[-1] if lines else "erreur inconnue"
    return f"Le téléchargement a échoué : {last}"


def _read_new(log: Path, offset: int) -> str:
    if not log.exists():
        return ""
    return log.read_bytes()[offset:].decode("utf-8", errors="replace")


def _cleanup(tmp: Path) -> None:
    shutil.rmtree(tmp, ignore_errors=True)


def _download(url: str, job: Path, log: Path, tmp: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise common.IdeoError("ffmpeg est introuvable : installez-le (par exemple avec brew install ffmpeg).")
    _cleanup(tmp)
    tmp.mkdir(parents=True)
    offset = log.stat().st_size if log.exists() else 0
    try:
        common.run(
            [
                sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-progress",
                "-f", "bestaudio[ext=m4a]/bestaudio",
                "-x", "--audio-format", "m4a",
                "--write-info-json",
                "-o", str(tmp / "audio.%(ext)s"),
                url,
            ],
            log,
        )
    except common.IdeoError as e:
        raise common.IdeoError(explain_ytdlp_error(_read_new(log, offset) + "\n" + str(e))) from e
    audio, info_file = tmp / "audio.m4a", tmp / "audio.info.json"
    if not audio.exists() or not info_file.exists():
        raise common.IdeoError(f"Le téléchargement n'a produit ni audio ni métadonnées. Voir {log}")
    raw = common.load_json(info_file)
    info = {k: raw.get(k) for k in INFO_FIELDS}
    info["chapters"] = info["chapters"] or []
    wav = tmp / "source.wav"
    common.run([ffmpeg, "-y", "-i", str(audio), "-vn", "-ac", "1", "-ar", "16000", str(wav)], log)
    if not wav.exists():
        raise common.IdeoError(f"La conversion audio a échoué. Voir {log}")
    common.save_json(job / "info.json", info)
    audio.replace(job / "source.m4a")
    wav.replace(job / "source.wav")


def fetch(url: str) -> Path:
    job = common.job_dir(url)
    status = common.read_status(job)["steps"].get("fetch", {})
    if (job / "source.wav").exists() and status.get("ok"):
        return job
    log = job / "logs" / "fetch.log"
    tmp = job / ".fetch-tmp"
    try:
        _download(url, job, log, tmp)
    except common.IdeoError as e:
        common.mark(job, "fetch", False, str(e))
        raise
    finally:
        _cleanup(tmp)
    common.mark(job, "fetch", True, "audio et métadonnées récupérés")
    return job
