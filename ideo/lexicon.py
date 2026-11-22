import json
import re
from pathlib import Path

from ideo import common

WORD = re.compile(r"\w+", re.UNICODE)
FILE = ("skills", "ideo", "references", "prononciation.json")
DEFAULT_LANG = "fr"


def path() -> Path:
    return common._root().joinpath(*FILE)


def _load(strict: bool = False) -> dict:
    file = path()
    if not file.exists():
        return {}
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("objet attendu")
    except (OSError, ValueError) as err:
        if strict:
            raise common.IdeoError(f"prononciation.json est illisible ({err}). Corrige le fichier {file}.") from err
        return {}
    return data


def _case(original: str, spoken: str) -> str:
    if len(original) > 1 and original.isupper():
        return spoken.upper()
    if original[:1].isupper():
        return spoken[:1].upper() + spoken[1:]
    return spoken


def entries(lang: str) -> dict:
    words = _load().get(lang)
    if not isinstance(words, dict):
        return {}
    return {k: v for k, v in words.items() if isinstance(k, str) and isinstance(v, str) and v.strip() and " " not in v}


def apply(text: str, lang: str) -> str:
    words = entries(lang)
    if not words:
        return text
    return WORD.sub(lambda m: _case(m.group(0), words[m.group(0).lower()]) if m.group(0).lower() in words else m.group(0), text)


def add(word: str, spoken: str, lang: str = DEFAULT_LANG) -> None:
    word, spoken = word.strip(), spoken.strip()
    if not word or not spoken:
        raise common.IdeoError("une prononciation s'écrit « mot=graphie » avec un mot et sa graphie, tous deux non vides.")
    if any(c.isspace() for c in word + spoken):
        raise common.IdeoError("une prononciation porte sur un seul mot, sans espace : écris « mot=graphie ».")
    data = _load(strict=True)
    data.setdefault(lang, {})[word.lower()] = spoken
    file = path()
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
