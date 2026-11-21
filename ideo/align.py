import difflib
import re

from ideo import textmatch

OPENERS = frozenset("«“‘([{¿¡")
ALNUM = re.compile(r"\w", re.UNICODE)


def script_words(text: str) -> list[str]:
    words: list[str] = []
    pending = ""
    for token in text.split():
        if not ALNUM.search(token):
            if token[0] in OPENERS:
                pending += token
            elif words:
                words[-1] += token
            else:
                pending += token
            continue
        words.append(pending + token)
        pending = ""
    if pending:
        if words:
            words[-1] += pending
        else:
            words.append(pending)
    return words


def _tokens(words: list[str]) -> list[tuple[int, str]]:
    out = []
    for i, w in enumerate(words):
        for part in textmatch.SPLIT.split(w):
            n = textmatch.normalize(part)
            if n:
                out.append((i, n))
    return out


def _spread(words: list[str], lo: float, hi: float) -> list[tuple[float, float]]:
    weights = [max(len(w), 1) for w in words]
    total = sum(weights)
    out, cursor = [], lo
    span = max(hi - lo, 0.0)
    for weight in weights:
        step = span * weight / total
        out.append((cursor, cursor + step))
        cursor += step
    return out


def align_words(script: list[str], recognised: list[dict], duration: float) -> list[dict]:
    if not script:
        return []
    a = _tokens(script)
    b = []
    for w in recognised:
        for part in textmatch.SPLIT.split(w["w"]):
            n = textmatch.normalize(part)
            if n:
                b.append((n, float(w["s"]), float(w["e"])))
    matcher = difflib.SequenceMatcher(None, [n for _, n in a], [n for n, _, _ in b], autojunk=False)
    times: list[tuple[float, float] | None] = [None] * len(script)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            idx = a[block.a + k][0]
            _, s, e = b[block.b + k]
            current = times[idx]
            times[idx] = (s, e) if current is None else (min(current[0], s), max(current[1], e))
    known = [i for i, t in enumerate(times) if t is not None]
    if not known:
        spread = _spread(script, 0.0, duration)
        times = list(spread)
    else:
        previous = -1
        for i in known + [len(script)]:
            if i - previous > 1:
                lo = times[previous][1] if previous >= 0 else 0.0
                hi = times[i][0] if i < len(script) else duration
                lo, hi = min(lo, hi), hi
                for k, slot in zip(range(previous + 1, i), _spread(script[previous + 1:i], lo, hi)):
                    times[k] = slot
            previous = i
    out = []
    floor = 0.0
    for word, (s, e) in zip(script, times):
        s = min(max(s, floor, 0.0), duration)
        e = min(max(e, s), duration)
        out.append({"w": word, "s": round(s, 3), "e": round(e, 3)})
        floor = s
    return out
