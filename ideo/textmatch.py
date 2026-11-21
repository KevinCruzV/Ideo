import re
import unicodedata

from ideo.common import fmt_ts

APOSTROPHES = "’‘ʼ`´"
LIGATURES = {"œ": "oe", "æ": "ae", "ß": "ss"}
SPLIT = re.compile("[\\s\\-" + "".join(chr(c) for c in range(0x2010, 0x2016)) + "]+")


def normalize(word: str) -> str:
    for a in APOSTROPHES:
        word = word.replace(a, "'")
    word = word.lower()
    for src, dst in LIGATURES.items():
        word = word.replace(src, dst)
    decomposed = unicodedata.normalize("NFKD", word)
    kept = "".join(c for c in decomposed if not unicodedata.combining(c) and (c.isalnum() or c == "'"))
    return kept.strip("'")


def _tokens(words: list[str]) -> list[tuple[int, str]]:
    out = []
    for i, w in enumerate(words):
        for part in SPLIT.split(w):
            n = normalize(part)
            if n:
                out.append((i, n))
    return out


def _needle(text: str) -> list[str]:
    return [n for _, n in _tokens([text])]


def find_span(words: list[str], needle: str, start: int = 0) -> tuple[int, int] | None:
    target = _needle(needle)
    if not target:
        return None
    hay = [(i, n) for i, n in _tokens(words) if i >= start]
    size = len(target)
    for k in range(len(hay) - size + 1):
        if all(hay[k + j][1] == target[j] for j in range(size)):
            return hay[k][0], hay[k + size - 1][0]
    return None


def closest_passage(words: list[dict], needle: str) -> str:
    target = _needle(needle)
    hay = _tokens([w["w"] for w in words])
    if not target or not hay:
        return ""
    size = min(len(target), len(hay))
    wanted = set(target)
    best, best_score = 0, -1
    for k in range(len(hay) - size + 1):
        chunk = hay[k:k + size]
        score = 10 * len(wanted & {n for _, n in chunk}) + (chunk[0][1] in wanted) + (chunk[-1][1] in wanted)
        if score > best_score:
            best, best_score = k, score
    chunk = hay[best:best + size]
    hits = [i for i, n in chunk if n in wanted]
    first = hits[0] if hits else chunk[0][0]
    last = hits[-1] if hits else chunk[-1][0]
    text = " ".join(w["w"] for w in words[first:last + 1])
    return f"[{fmt_ts(words[first]['s'])}] {text}"
