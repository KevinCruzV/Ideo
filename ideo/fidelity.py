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


def best(scores: list[float]) -> int:
    return max(range(len(scores)), key=lambda i: scores[i])
