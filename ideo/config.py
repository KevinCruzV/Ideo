import json
import re

from ideo import common

DEFAULT_RATE = "+0%"
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
    return data


def rate() -> str:
    return _load().get("rate", DEFAULT_RATE)


def voice_for(lang: str) -> str | None:
    from ideo import voice

    override = _load().get("voices", {}).get(lang)
    return override or voice.EDGE_VOICES.get(lang)
