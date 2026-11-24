import re
import unicodedata
from pathlib import Path

from ideo import common

SIGNALES = "Défauts signalés"
DETECTES = "Défauts détectés"
DESSINS = "Dessins manquants"
SECTIONS = (SIGNALES, DETECTES, DESSINS)
TITLE = "# Retours"
INTRO = ("Une entrée par ligne : `- [ ]` à traiter, `- [x]` traitée. Les défauts signalés viennent de `python -m ideo learn --bug`, "
         "les défauts détectés du contrôle après fabrication, les dessins manquants du champ `wishes` des plans.")
ENTRY = re.compile(r"^- \[( |x)\] (.*)$")
COUNT = re.compile(r"^(.*?)(?: \(×(\d+)\))?$")
OLD = re.compile(r"^- \[(?! |x\])(.*)$")


def path() -> Path:
    return common._root() / "retours.md"


def _parse() -> dict:
    sections = {name: [] for name in SECTIONS}
    file = path()
    if file.exists():
        current = None
        for line in file.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                sections.setdefault(current, [])
            elif ENTRY.match(line):
                sections[current or SIGNALES].append(line)
            elif OLD.match(line):
                sections[current or SIGNALES].append("- [ ] [" + OLD.match(line).group(1))
            elif line.startswith("  ") and line.strip() and sections.get(current):
                sections[current].append(line.rstrip())
    return sections


def _write(sections: dict) -> None:
    lines = [TITLE, "", INTRO, ""]
    for name, entries in sections.items():
        lines += [f"## {name}", ""] + entries + ([""] if entries else [])
    path().write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


def _safe(default):
    def wrap(fn):
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except OSError:
                return default
        return inner
    return wrap


def add(section: str, text: str) -> None:
    sections = _parse()
    sections.setdefault(section, []).append(f"- [ ] {text}")
    _write(sections)


def _entries(section: str | None = None, only_open: bool = True) -> list[str]:
    sections = _parse()
    names = [section] if section else list(sections)
    out = []
    for name in names:
        for line in sections.get(name, []):
            m = ENTRY.match(line)
            if m and (m.group(1) == " " or not only_open):
                out.append(m.group(2))
    return out


@_safe([])
def unchecked(section: str | None = None) -> list[str]:
    return _entries(section)


@_safe(0)
def count_unchecked() -> int:
    return len(_entries())


def _key(text: str) -> str:
    plain = "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))
    return " ".join(re.sub(r"[\W_]+", " ", plain).split())


def add_wish(text: str) -> None:
    text = " ".join(text.split())
    sections = _parse()
    entries = sections.setdefault(DESSINS, [])
    for i, line in enumerate(entries):
        m = ENTRY.match(line)
        if m and m.group(1) == " ":
            base, count = COUNT.match(m.group(2)).groups()
            if _key(base) == _key(text):
                entries[i] = f"- [ ] {base} (×{int(count or 1) + 1})"
                _write(sections)
                return
    entries.append(f"- [ ] {text}")
    _write(sections)


@_safe([])
def wishes() -> list[tuple[str, int]]:
    out = []
    for entry in _entries(DESSINS):
        base, count = COUNT.match(entry).groups()
        out.append((base, int(count or 1)))
    return sorted(out, key=lambda pair: -pair[1])


def add_detected(code: str, job: str, message: str) -> bool:
    tag = f"`{code}`"
    if any(entry.startswith(tag) for entry in _entries(DETECTES)):
        return False
    add(DETECTES, f"{tag} ({job}) {message}")
    return True
