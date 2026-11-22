import base64
import json
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ideo import common, config

API_BASE = "https://api.elevenlabs.io"
TIMEOUT = 180
RETRY_BELOW = 0.80
ADDED_WORD_SCORE = 0.79
MASK = "***"
DEFAULT_TEST = "Bonjour, ceci est un essai de la voix choisie."
SETUP_HELP = ("Mets ta clé dans la variable d'environnement ELEVENLABS_API_KEY ou dans config.json (« elevenlabs_api_key »), "
              "puis lance « python -m ideo voix-liste » pour choisir une voix.")


def _mask(text: str, key: str | None) -> str:
    text = str(text)
    if key:
        text = text.replace(key, MASK)
    return re.sub(r"(xi-api-key['\": =]+)[\w-]+", rf"\1{MASK}", text, flags=re.IGNORECASE)


def _require_key() -> str:
    key = config.eleven_key()
    if not key:
        raise common.IdeoError("la clé ElevenLabs est absente (ELEVENLABS_API_KEY). " + SETUP_HELP)
    return key


def _request(method: str, path: str, key: str, body: dict | None = None) -> tuple[dict, dict]:
    url = API_BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"xi-api-key": key, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8")), dict(response.headers.items())
    except urllib.error.HTTPError as err:
        detail = ""
        try:
            detail = _mask(err.read().decode("utf-8", "replace"), key)[:200]
        except OSError:
            pass
        if err.code == 401:
            reason = "la clé ElevenLabs est refusée (401). Vérifie-la sur elevenlabs.io."
        elif err.code in (402, 429):
            reason = f"quota ElevenLabs épuisé ou trop de requêtes ({err.code}). Vérifie ton abonnement."
        elif err.code == 404:
            reason = "voix ElevenLabs introuvable (404). Lance « python -m ideo voix-liste » pour choisir une voix."
        else:
            reason = f"ElevenLabs a répondu {err.code}"
        raise common.IdeoError(f"{reason} {detail}".strip()) from None
    except urllib.error.URLError as err:
        raise common.IdeoError(f"connexion à ElevenLabs impossible : {_mask(err.reason, key)}") from None
    except (OSError, ValueError) as err:
        raise common.IdeoError(f"réponse ElevenLabs illisible : {_mask(err, key)}") from None


def words_from_alignment(alignment: dict | None) -> list[dict] | None:
    if not isinstance(alignment, dict):
        return None
    chars = alignment.get("characters")
    starts = alignment.get("character_start_times_seconds")
    ends = alignment.get("character_end_times_seconds")
    if not (isinstance(chars, list) and isinstance(starts, list) and isinstance(ends, list)) or not len(chars) == len(starts) == len(ends):
        return None
    words, current = [], None
    for ch, start, end in zip(chars, starts, ends):
        if not isinstance(ch, str) or ch.isspace():
            if current:
                words.append(current)
                current = None
            continue
        if current is None:
            current = {"w": ch, "s": float(start), "e": float(end)}
        else:
            current["w"] += ch
            current["e"] = float(end)
    if current:
        words.append(current)
    return [{"w": w["w"], "s": round(w["s"], 4), "e": round(w["e"], 4)} for w in words] or None


class ElevenLabsBackend:
    local = False
    paid = True

    def __init__(self, log: Path | None = None):
        self.log = log
        self.voice = config.eleven_voice_id()
        if not self.voice:
            raise common.IdeoError("ElevenLabs demande une voix : lance « python -m ideo voix-liste » pour voir celles de ton compte, "
                                   "puis mets son identifiant dans config.json sous « elevenlabs_voice_id ».")
        self.characters = 0
        self.request_ids: list[str] = []

    def _body(self, text: str, previous_text: str | None, next_text: str | None) -> dict:
        settings = config.eleven_settings()
        body = {
            "text": text,
            "model_id": config.eleven_model(),
            "voice_settings": {"stability": settings["stability"], "similarity_boost": settings["similarity"],
                               "style": settings["style"], "speed": settings["speed"], "use_speaker_boost": True},
        }
        if self.request_ids:
            body["previous_request_ids"] = self.request_ids[-3:]
        elif previous_text:
            body["previous_text"] = previous_text
        if next_text:
            body["next_text"] = next_text
        return body

    def synthesize(self, text: str, lang: str, out_wav: Path, previous_text: str | None = None,
                   next_text: str | None = None) -> list[dict] | None:
        key = _require_key()
        out_wav = Path(out_wav)
        path = f"/v1/text-to-speech/{urllib.parse.quote(self.voice)}/with-timestamps"
        data, headers = _request("POST", path, key, self._body(text, previous_text, next_text))
        self.characters += len(text)
        request_id = next((v for k, v in headers.items() if k.lower() == "request-id"), None)
        if request_id:
            self.request_ids.append(request_id)
        audio = data.get("audio_base64")
        if not isinstance(audio, str) or not audio:
            raise common.IdeoError("ElevenLabs n'a renvoyé aucun audio.")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "voice.audio"
            source.write_bytes(base64.b64decode(audio))
            common.run(["ffmpeg", "-y", "-i", str(source), "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(out_wav)],
                       self.log or out_wav.parent / "ffmpeg.log")
        return words_from_alignment(data.get("alignment"))


def list_voices() -> list[dict]:
    key = _require_key()
    out, token = [], None
    for _ in range(20):
        query = "page_size=100" + (f"&next_page_token={urllib.parse.quote(token)}" if token else "")
        data, _ = _request("GET", f"/v2/voices?{query}", key)
        for voice in data.get("voices") or []:
            labels = voice.get("labels") if isinstance(voice.get("labels"), dict) else {}
            detail = ", ".join(str(v) for k in ("language", "accent", "gender", "age") if (v := labels.get(k)))
            out.append({"name": voice.get("name", "?"), "id": voice.get("voice_id", "?"), "detail": detail})
        token = data.get("next_page_token")
        if not data.get("has_more") or not token:
            break
    return out


def try_phrase(text: str, destination: Path) -> tuple[int, float]:
    backend = ElevenLabsBackend(destination.parent / "voix-test.log")
    backend.synthesize(text, "fr", destination)
    import wave

    with wave.open(str(destination), "rb") as w:
        return backend.characters, w.getnframes() / w.getframerate()
