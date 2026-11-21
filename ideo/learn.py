import re
from datetime import date
from pathlib import Path

from ideo import common

MAX_LESSONS = 40
MAX_LENGTH = 200
EM_DASH = chr(0x2014)
TITLE = "# Leçons apprises"
INTRO = ("Une règle par ligne, au format `- [AAAA-MM-JJ] règle`. Le skill relit ces leçons avant d'écrire un plan : "
         "ajoute-les avec `python -m ideo learn \"<leçon>\"`.")
RETOURS_TITLE = "# Retours"
RETOURS_INTRO = "Défauts que seul un changement de code peut corriger, ajoutés avec `python -m ideo learn --bug`."
LESSON = re.compile(r"^- \[\d{4}-\d{2}-\d{2}\] (.+)$")


def lessons_path() -> Path:
    return common._root() / "skills" / "ideo" / "references" / "lecons.md"


def retours_path() -> Path:
    return common._root() / "retours.md"


def _plain(text: str) -> str:
    return " ".join(re.sub(r"[\W_]+", " ", text.lower()).split())


def existing(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [m.group(1) for line in path.read_text(encoding="utf-8").splitlines() if (m := LESSON.match(line))]


def _clean(text: str, what: str) -> str:
    text = " ".join(text.split())
    if not text:
        raise common.IdeoError(f"{what} est vide : écris-la en une phrase.")
    if EM_DASH in text:
        raise common.IdeoError(f"{what} contient un tiret cadratin : remplace-le par une virgule, deux-points ou un point.")
    return text


def add_lesson(text: str) -> tuple[int, Path]:
    text = _clean(text, "la leçon")
    if len(text) > MAX_LENGTH:
        raise common.IdeoError(f"la leçon fait {len(text)} caractères, {MAX_LENGTH} au plus : écris une règle en une phrase.")
    path = lessons_path()
    known = existing(path)
    if any(_plain(k) == _plain(text) for k in known):
        raise common.IdeoError("cette leçon existe déjà : ne l'ajoute pas deux fois.")
    if len(known) >= MAX_LESSONS:
        raise common.IdeoError(f"{MAX_LESSONS} leçons déjà enregistrées : fusionne ou retire des leçons dans {path} "
                               "avant d'en ajouter.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"{TITLE}\n\n{INTRO}\n\n", encoding="utf-8")
    body = path.read_text(encoding="utf-8")
    if not body.endswith("\n"):
        body += "\n"
    path.write_text(f"{body}- [{date.today().isoformat()}] {text}\n", encoding="utf-8")
    return len(known) + 1, path


def add_bug(text: str, job: str | None = None) -> Path:
    text = _clean(text, "le constat")
    path = retours_path()
    if not path.exists():
        path.write_text(f"{RETOURS_TITLE}\n\n{RETOURS_INTRO}\n\n", encoding="utf-8")
    body = path.read_text(encoding="utf-8")
    if not body.endswith("\n"):
        body += "\n"
    tag = f" ({job})" if job else ""
    path.write_text(f"{body}- [{date.today().isoformat()}]{tag} {text}\n", encoding="utf-8")
    return path
