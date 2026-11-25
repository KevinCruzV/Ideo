import difflib
import re

from ideo import textmatch

NUMBER_WORDS = frozenset({
    "zero", "un", "une", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze",
    "treize", "quatorze", "quinze", "seize", "vingt", "trente", "quarante", "cinquante", "soixante", "cent", "cents",
    "mille", "million", "millions", "milliard", "milliards", "et",
    "one", "two", "three", "four", "five", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety", "hundred", "thousand", "billion", "billions",
})
SPELLED = frozenset(NUMBER_WORDS - {"et", "un", "une", "one", "six", "cent"})
NUMERIC = re.compile(r"^\d+$")


def _tokens(text: str) -> list[str]:
    out = []
    for part in textmatch.SPLIT.split(text):
        n = textmatch.normalize(part)
        if n:
            out.append(n)
    return out


def _is_number(token: str, around: list[str], i: int) -> bool:
    if NUMERIC.match(token):
        return True
    if token not in NUMBER_WORDS:
        return False
    if token in SPELLED:
        return True
    neighbours = around[max(0, i - 1):i] + around[i + 1:i + 2]
    return any(n in SPELLED or NUMERIC.match(n) for n in neighbours)


def _clean(tokens: list[str]) -> list[str]:
    return [t for i, t in enumerate(tokens) if not _is_number(t, tokens, i)]


def similarity(text: str, heard: list[dict]) -> float:
    expected = _clean(_tokens(text))
    got = _clean(_tokens(" ".join(w["w"] for w in heard)))
    if not expected:
        return 1.0
    if not got:
        return 0.0
    return round(difflib.SequenceMatcher(None, expected, got, autojunk=False).ratio(), 4)


def added(text: str, heard: list[dict]) -> list[str]:
    expected = _clean(_tokens(text))
    got = _clean(_tokens(" ".join(w["w"] for w in heard)))
    extra: list[str] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, expected, got, autojunk=False).get_opcodes():
        if tag == "insert":
            extra += got[j1:j2]
        elif tag == "replace" and j2 - j1 > i2 - i1:
            extra += got[j2 - ((j2 - j1) - (i2 - i1)):j2]
    return extra


def keep_count(text: str, heard: list[dict]) -> int | None:
    expected = _clean(_tokens(text))
    owners, tokens = [], []
    for i, w in enumerate(heard):
        for t in _tokens(w["w"]):
            owners.append(i)
            tokens.append(t)
    kept = [k for k, t in enumerate(tokens) if not _is_number(t, tokens, k)]
    got = [tokens[k] for k in kept]
    ops = difflib.SequenceMatcher(None, expected, got, autojunk=False).get_opcodes()
    tail = []
    for tag, i1, i2, j1, j2 in reversed(ops):
        if tag == "insert" or (tag == "replace" and j2 - j1 > i2 - i1):
            tail.append((tag, i1, i2, j1, j2))
            if tag == "replace":
                break
        else:
            break
    last = ops[-1] if ops else None
    if not tail or last is None or last[4] != len(got):
        return None
    tag, i1, i2, j1, j2 = tail[-1]
    first_extra = j1 if tag == "insert" else j1 + (i2 - i1)
    if first_extra <= 0:
        return None
    return owners[kept[first_extra - 1]] + 1


def best(scores: list[float]) -> int:
    return max(range(len(scores)), key=lambda i: scores[i])
