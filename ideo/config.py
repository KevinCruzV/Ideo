import json
import platform
import re
from pathlib import Path

from ideo import common

DEFAULT_RATE = "+0%"
DEFAULT_SEUIL = 5
KYUTAI_LANGS = ("fr", "en")
ENGINES = ("kyutai", "edge")
KYUTAI_PYTHON = common.REPO_ROOT / ".venv-voix2" / "bin" / "python"
DEFAULT_KYUTAI_VOICE = "unmute-prod-website/developpeuse-3.wav"
DEFAULT_PADDING_BONUS = 0.5
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
        raise common.IdeoError("config.json : « engine » doit valoir « kyutai » ou « edge ».")
    voice = data.get("kyutai_voice", DEFAULT_KYUTAI_VOICE)
    if not isinstance(voice, str) or not voice.strip():
        raise common.IdeoError("config.json : « kyutai_voice » doit être le nom d'une voix, par exemple "
                               "« unmute-prod-website/developpeuse-3.wav ».")
    bonus = data.get("kyutai_padding_bonus", DEFAULT_PADDING_BONUS)
    if isinstance(bonus, bool) or not isinstance(bonus, (int, float)) or not -2 <= bonus <= 2:
        raise common.IdeoError("config.json : « kyutai_padding_bonus » doit être un nombre entre -2 et 2 "
                               "(positif = voix plus lente).")
    return data


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


def kyutai_available() -> bool:
    return apple_silicon() and kyutai_installed()


def local_voice_missing(lang: str) -> bool:
    if lang not in KYUTAI_LANGS or not apple_silicon() or kyutai_installed():
        return False
    return _load().get("engine") != "edge"


def engine() -> str:
    chosen = _load().get("engine")
    if chosen:
        return chosen
    return "kyutai" if kyutai_available() else "edge"


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
