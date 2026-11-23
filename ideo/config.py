import json
import platform
import re
from pathlib import Path

from ideo import common

DEFAULT_RATE = "+0%"
DEFAULT_SEUIL = 5
DEFAULT_MUSIC_LEVEL = -23
KYUTAI_LANGS = ("fr", "en")
ENGINES = ("kyutai", "edge", "elevenlabs")
DEFAULT_ELEVEN_MODEL = "eleven_multilingual_v2"
DEFAULT_ELEVEN_VOICE = "cgSgspJ2msm6clMCkdW9"
ELEVEN_DEFAULTS = {"stability": 0.45, "similarity": 0.8, "style": 0.3, "speed": 1.0}
DEFAULT_TRANSITION_DB = -12
KYUTAI_PYTHON = common.REPO_ROOT / ".venv-voix2" / "bin" / "python"
DEFAULT_KYUTAI_VOICE = "unmute-prod-website/developpeuse-3.wav"
DEFAULT_PADDING_BONUS = 0.5
DEFAULT_HOOK_TEMP = 0.95
DEFAULT_HOOK_PADDING = -0.4
RATE = re.compile(r"^[+-]\d{1,3}%$")


def _load() -> dict:
    path = common._root() / "config.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as err:
        raise common.IdeoError(f"config.json n'est pas un JSON valide ({err}). Corrige la syntaxe ou supprime le fichier.") from err
    except OSError as err:
        raise common.IdeoError(f"config.json est illisible ({err}). Vérifie le fichier ou supprime-le.") from err
    if not isinstance(data, dict):
        raise common.IdeoError("config.json doit contenir un objet JSON, par exemple {\"rate\": \"+0%\"}.")
    voices = data.get("voices", {})
    if not isinstance(voices, dict) or any(
        not isinstance(k, str) or not isinstance(v, str) or not v.strip() for k, v in voices.items()
    ):
        raise common.IdeoError("config.json : « voices » doit associer un code de langue à un nom de voix edge-tts, "
                               "par exemple {\"voices\": {\"fr\": \"fr-FR-DeniseNeural\"}}.")
    rate = data.get("rate", DEFAULT_RATE)
    if not isinstance(rate, str) or not RATE.match(rate):
        raise common.IdeoError("config.json : « rate » doit être un texte comme « +0% » ou « -5% ».")
    auto = data.get("entretien_auto", True)
    if not isinstance(auto, bool):
        raise common.IdeoError("config.json : « entretien_auto » doit être true ou false.")
    seuil = data.get("entretien_seuil", DEFAULT_SEUIL)
    if isinstance(seuil, bool) or not isinstance(seuil, int) or seuil < 1:
        raise common.IdeoError("config.json : « entretien_seuil » doit être un nombre entier d'au moins 1.")
    engine = data.get("engine")
    if engine is not None and engine not in ENGINES:
        raise common.IdeoError("config.json : « engine » doit valoir « kyutai », « edge » ou « elevenlabs ».")
    for key in ("elevenlabs_api_key", "elevenlabs_voice_id", "elevenlabs_model"):
        value = data.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise common.IdeoError(f"config.json : « {key} » doit être un texte non vide.")
    for key, (low, high) in {"stability": (0, 1), "similarity": (0, 1), "style": (0, 1), "speed": (0.7, 1.2)}.items():
        value = data.get(f"elevenlabs_{key}", ELEVEN_DEFAULTS[key])
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
            raise common.IdeoError(f"config.json : « elevenlabs_{key} » doit être un nombre entre {low} et {high}.")
    transition = data.get("transition_sfx", True)
    if not isinstance(transition, bool):
        raise common.IdeoError("config.json : « transition_sfx » doit être true ou false.")
    transition_db = data.get("transition_sfx_db", DEFAULT_TRANSITION_DB)
    if isinstance(transition_db, bool) or not isinstance(transition_db, (int, float)) or not -40 <= transition_db <= 0:
        raise common.IdeoError("config.json : « transition_sfx_db » doit être un nombre entre -40 et 0 "
                               "(niveau des sons de transition sous la voix, en dB).")
    voice = data.get("kyutai_voice", DEFAULT_KYUTAI_VOICE)
    if not isinstance(voice, str) or not voice.strip():
        raise common.IdeoError("config.json : « kyutai_voice » doit être le nom d'une voix, par exemple "
                               "« unmute-prod-website/developpeuse-3.wav ».")
    bonus = data.get("kyutai_padding_bonus", DEFAULT_PADDING_BONUS)
    if isinstance(bonus, bool) or not isinstance(bonus, (int, float)) or not -2 <= bonus <= 2:
        raise common.IdeoError("config.json : « kyutai_padding_bonus » doit être un nombre entre -2 et 2 "
                               "(positif = voix plus lente).")
    hook_temp = data.get("kyutai_hook_temp", DEFAULT_HOOK_TEMP)
    if isinstance(hook_temp, bool) or not isinstance(hook_temp, (int, float)) or not 0.1 <= hook_temp <= 1.5:
        raise common.IdeoError("config.json : « kyutai_hook_temp » doit être un nombre entre 0,1 et 1,5 "
                               "(température de l'accroche et de la phrase de fin).")
    hook_padding = data.get("kyutai_hook_padding_bonus", DEFAULT_HOOK_PADDING)
    if isinstance(hook_padding, bool) or not isinstance(hook_padding, (int, float)) or not -2 <= hook_padding <= 2:
        raise common.IdeoError("config.json : « kyutai_hook_padding_bonus » doit être un nombre entre -2 et 2 "
                               "(positif = voix plus lente, pour l'accroche et la phrase de fin).")
    music = data.get("music", True)
    if not isinstance(music, bool):
        raise common.IdeoError("config.json : « music » doit être true ou false.")
    folder = data.get("music_dir")
    if folder is not None and (not isinstance(folder, str) or not folder.strip()):
        raise common.IdeoError("config.json : « music_dir » doit être le chemin d'un dossier de musique.")
    level = data.get("music_level_db", DEFAULT_MUSIC_LEVEL)
    if isinstance(level, bool) or not isinstance(level, (int, float)) or not -40 <= level <= -5:
        raise common.IdeoError("config.json : « music_level_db » doit être un nombre entre -40 et -5 "
                               "(niveau de la musique sous la voix, en dB).")
    return data


def music_enabled() -> bool:
    return _load().get("music", False)


def eleven_key() -> str | None:
    import os

    from dotenv import dotenv_values

    env_file = common._root() / ".env"
    from_dotenv = dotenv_values(env_file).get("ELEVENLABS_API_KEY") if env_file.exists() else None
    return ((os.environ.get("ELEVENLABS_API_KEY") or "").strip() or (from_dotenv or "").strip()
            or _load().get("elevenlabs_api_key"))


def eleven_voice_id() -> str | None:
    return _load().get("elevenlabs_voice_id", DEFAULT_ELEVEN_VOICE)


def eleven_model() -> str:
    return _load().get("elevenlabs_model", DEFAULT_ELEVEN_MODEL)


def eleven_settings() -> dict:
    data = _load()
    return {key: data.get(f"elevenlabs_{key}", default) for key, default in ELEVEN_DEFAULTS.items()}


def transition_sfx_enabled() -> bool:
    return _load().get("transition_sfx", True)


def transition_sfx_db() -> float:
    return _load().get("transition_sfx_db", DEFAULT_TRANSITION_DB)


def music_dir() -> Path:
    folder = _load().get("music_dir")
    path = Path(folder).expanduser() if folder else common._root() / "musique"
    return path if path.is_absolute() else common._root() / path


def music_level_db() -> float:
    return _load().get("music_level_db", DEFAULT_MUSIC_LEVEL)


def apple_silicon() -> bool:
    return platform.machine() == "arm64"


def kyutai_env() -> Path:
    return Path(KYUTAI_PYTHON).parent.parent


def install_lock() -> Path:
    env = kyutai_env()
    return env.with_name(env.name + ".installing")


def kyutai_installed() -> bool:
    if not Path(KYUTAI_PYTHON).exists() or install_lock().exists():
        return False
    return any(kyutai_env().glob("lib/python*/site-packages/moshi_mlx"))


def kyutai_hook_temp() -> float:
    return _load().get("kyutai_hook_temp", DEFAULT_HOOK_TEMP)


def kyutai_hook_padding_bonus() -> float:
    return _load().get("kyutai_hook_padding_bonus", DEFAULT_HOOK_PADDING)


def kyutai_available() -> bool:
    return apple_silicon() and kyutai_installed()


def local_voice_missing(lang: str) -> bool:
    if lang not in KYUTAI_LANGS or not apple_silicon() or kyutai_installed():
        return False
    return _load().get("engine") != "edge"


FINAL_FILE = "voix-finale.json"
FREE_ENGINES = ("kyutai", "edge")


def final_engine() -> str:
    chosen = _load().get("engine")
    if chosen:
        return chosen
    if eleven_key():
        return "elevenlabs"
    return "kyutai" if kyutai_available() else "edge"


def draft_engine() -> str:
    chosen = _load().get("engine")
    if chosen in FREE_ENGINES:
        return chosen
    return "kyutai" if kyutai_available() else "edge"


def is_final(job: Path) -> bool:
    return (Path(job) / FINAL_FILE).exists()


def mark_final(job: Path) -> None:
    (Path(job) / FINAL_FILE).write_text(json.dumps({"engine": final_engine()}) + "\n", encoding="utf-8")


def engine(job: Path | None = None) -> str:
    if job is None or is_final(job):
        return final_engine()
    return draft_engine()


def kyutai_voice() -> str:
    return _load().get("kyutai_voice", DEFAULT_KYUTAI_VOICE)


def kyutai_padding_bonus() -> float:
    return _load().get("kyutai_padding_bonus", DEFAULT_PADDING_BONUS)


def entretien_auto() -> bool:
    return _load().get("entretien_auto", True)


def entretien_seuil() -> int:
    return _load().get("entretien_seuil", DEFAULT_SEUIL)


def rate() -> str:
    return _load().get("rate", DEFAULT_RATE)


def voice_for(lang: str) -> str | None:
    from ideo import voice

    override = _load().get("voices", {}).get(lang)
    return override or voice.EDGE_VOICES.get(lang)
