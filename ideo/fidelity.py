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
SENTENCE_END = (".", "!", "?", "…")
CLOSERS = "»”\"')]"
NAME_MATCH = 0.7
OPENER_MATCH = 0.6
NAME_WINDOW = 3
SPLIT_MIN = 6


def _tokens(text: str) -> list[str]:
    out = []
    for part in textmatch.SPLIT.split(text):
        n = textmatch.normalize(part)
        if n:
            out.append(n)
    return out


def _names(text: str) -> list[str]:
    out = []
    initial = True
    for chunk in text.split():
        for k, part in enumerate(textmatch.SPLIT.split(chunk)):
            n = textmatch.normalize(part)
            letters = [c for c in part if c.isalpha()]
            if n and letters and letters[0].isupper() and len(letters) >= 3 and not (initial and k == 0):
                out.append(n)
        initial = chunk.rstrip(CLOSERS).endswith(SENTENCE_END)
    return out


def _opener(text: str) -> list[str]:
    chunks = text.split()
    if not chunks:
        return []
    first = textmatch.SPLIT.split(chunks[0])[0]
    letters = [c for c in first if c.isalpha()]
    n = textmatch.normalize(first)
    return [n] if n and len(letters) >= 3 and letters[0].isupper() else []


def _fold(names: list[str], tokens: list[str], owners: list[int] | None = None, smallest: int = 1,
          match: float = NAME_MATCH) -> tuple[list[str], list[int] | None]:
    tokens = list(tokens)
    owners = list(owners) if owners is not None else None
    wanted = set(names)
    for name in names:
        if tokens.count(name) >= names.count(name):
            continue
        best = None
        for size in range(smallest, NAME_WINDOW + 1):
            for k in range(len(tokens) - size + 1):
                window = tokens[k:k + size]
                if name in window or (size == 1 and window[0] in wanted):
                    continue
                score = difflib.SequenceMatcher(None, name, "".join(window)).ratio()
                if score >= match and (best is None or score > best[0]):
                    best = (score, k, size)
        if best:
            _, k, size = best
            tokens[k:k + size] = [name]
            if owners is not None:
                owners[k:k + size] = [owners[k + size - 1]]
    return tokens, owners


def _settle(text: str, tokens: list[str], owners: list[int] | None = None) -> tuple[list[str], list[int] | None]:
    names = _names(text)
    tokens, owners = _fold(names, tokens, owners)
    head = owners[:NAME_WINDOW] if owners is not None else None
    start, head = _fold(_opener(text), tokens[:NAME_WINDOW], head, smallest=2, match=OPENER_MATCH)
    tokens = start + tokens[NAME_WINDOW:]
    if owners is not None:
        owners = head + owners[NAME_WINDOW:]
    words = [t for t in _tokens(text) if len(t) >= SPLIT_MIN and t not in names]
    return _fold(words, tokens, owners, smallest=2, match=1.0)


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


def _compare(text: str, heard: list[dict]) -> tuple[list[str], list[str]]:
    got, _ = _settle(text, _tokens(" ".join(w["w"] for w in heard)))
    return _clean(_tokens(text)), _clean(got)


def similarity(text: str, heard: list[dict]) -> float:
    expected, got = _compare(text, heard)
    if not expected:
        return 1.0
    if not got:
        return 0.0
    return round(difflib.SequenceMatcher(None, expected, got, autojunk=False).ratio(), 4)


def added(text: str, heard: list[dict]) -> list[str]:
    expected, got = _compare(text, heard)
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
    tokens, owners = _settle(text, tokens, owners)
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
