import json
import sys
import tempfile
import time
from pathlib import Path

from ideo import common, config

MODEL_REPO = "kyutai/tts-1.6b-en_fr"
VOICE_REPO = "kyutai/tts-voices"
DOWNLOAD_GB = 4.3
SAMPLE = "Bonjour, ceci est un test de la voix locale."
DOWNLOAD_CODE = """
import json, sys
from huggingface_hub import hf_hub_download, snapshot_download
repo, voice_repo, voice = sys.argv[1:4]
with open(hf_hub_download(repo, "config.json")) as f:
    cfg = json.load(f)
for key, default in (("mimi_name", None), ("moshi_name", "model.safetensors"), ("tokenizer_name", None)):
    name = cfg.get(key, default)
    if name:
        hf_hub_download(repo, name)
snapshot_download(repo_id=voice_repo, allow_patterns=[voice + "*"])
"""


def size_text(gigabytes: float = DOWNLOAD_GB) -> str:
    halves = round(gigabytes * 2) / 2
    return f"{halves:g}".replace(".", ",")


def install_note(lang: str) -> str:
    if config.local_voice_missing(lang):
        return f" Voix locale : à installer (environ {size_text()} Go)."
    return ""


def _fmt(seconds: float) -> str:
    seconds = round(seconds)
    if seconds < 60:
        return f"{seconds} s"
    return f"{seconds // 60} min {seconds % 60} s"


def log_path() -> Path:
    return common._root() / "logs" / "setup-voix.log"


def marker() -> Path:
    return config.kyutai_env() / "ideo-voix.json"


def ready() -> bool:
    if not config.kyutai_installed() or not marker().exists():
        return False
    try:
        return common.load_json(marker()).get("voice") == config.kyutai_voice()
    except (OSError, ValueError, AttributeError):
        return False


def _run(cmd: list, log: Path, step: str) -> None:
    try:
        common.run([str(c) for c in cmd], log)
    except common.IdeoError as err:
        raise common.IdeoError(
            f"{step} a échoué ({err}). Vérifie la connexion internet puis relance « python -m ideo setup-voix », "
            f"ou mets « engine »: « edge » dans config.json pour garder la voix en ligne."
        ) from err


def _verify(log: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        jsonl = work / "check.jsonl"
        jsonl.write_text(json.dumps({"id": "check", "turns": [SAMPLE], "voices": [config.kyutai_voice()]},
                                    ensure_ascii=False) + "\n", encoding="utf-8")
        _run([config.KYUTAI_PYTHON, "-m", "moshi_mlx.run_tts", jsonl, "--out-folder", work / "out", "--only-wav"], log,
             "la synthèse de vérification")
        wav = work / "out" / "check.wav"
        if not wav.exists() or wav.stat().st_size == 0:
            raise common.IdeoError(f"la synthèse de vérification n'a rien produit. Voir {log}")


def run() -> str:
    if not config.apple_silicon():
        raise common.IdeoError("la voix locale demande un Mac à puce Apple. La voix en ligne sera utilisée.")
    if ready():
        return "voix locale déjà prête, rien à faire"
    start = time.time()
    log = log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    env = config.kyutai_env()
    tools = env.parent / ".venv-tools"
    lock = config.install_lock()
    lock.write_text("installation en cours\n", encoding="utf-8")
    try:
        if not (tools / "bin" / "python").exists():
            _run([sys.executable, "-m", "venv", tools], log, "la création de l'outil d'installation")
        if not (tools / "bin" / "uv").exists():
            _run([tools / "bin" / "pip", "install", "-q", "uv"], log, "l'installation de uv")
        if not Path(config.KYUTAI_PYTHON).exists():
            _run([tools / "bin" / "uv", "venv", "--python", "3.12", env], log, "la création de l'environnement de voix")
        if not any(env.glob("lib/python*/site-packages/moshi_mlx")):
            _run([tools / "bin" / "uv", "pip", "install", "--python", config.KYUTAI_PYTHON, "moshi_mlx"], log,
                 "l'installation de moshi_mlx")
        _run([config.KYUTAI_PYTHON, "-c", DOWNLOAD_CODE, MODEL_REPO, VOICE_REPO, config.kyutai_voice()], log,
             "le téléchargement du modèle et de la voix")
        lock.unlink(missing_ok=True)
        _verify(log)
        common.save_json(marker(), {"voice": config.kyutai_voice(), "model": MODEL_REPO})
    finally:
        lock.unlink(missing_ok=True)
    return f"voix locale prête ({_fmt(time.time() - start)})"
