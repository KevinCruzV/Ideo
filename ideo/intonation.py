import wave
from pathlib import Path

import numpy as np

ANYWHERE = {
    "fr": {"pourquoi", "comment", "combien", "quoi", "quel", "quelle", "quels", "quelles", "lequel", "laquelle",
           "lesquels", "lesquelles", "qu'est-ce"},
    "en": {"why", "how", "what", "which", "whose"},
}
CLAUSE_START = {
    "fr": {"qui", "où", "quand"},
    "en": {"who", "whom", "where", "when"},
}
LINKS = {"fr": {"et", "mais", "alors", "donc"}, "en": {"and", "but", "so"}}
CHOICE = {"fr": "ou", "en": "or"}
STRIP = "   .,;:!?…«»\"“”()"
SENTENCE_END = (".", "!", "?", "…")

KEEP = 0.5
PEAK = 7.0
AFTER_PEAK = 2.0
RISE = 7.0
RISE_SPAN = 0.25
PEAK_MIN = 5.0
RISE_MIN = 5.0
EDGE = 0.06
TAIL_GUARD = 0.08
SPLICE_BEFORE = 0.05
SPLICE_AFTER = 0.1
FADE = 0.01
TIME_STEP = 0.01
FLOOR = 75
CEILING = 500


def _clean(token: str) -> str:
    return token.replace("’", "'").lower().strip(STRIP)


def _bare(token: str) -> bool:
    return not _clean(token)


def kind(tokens: list[str], lang: str) -> tuple[str, int | None] | None:
    if lang not in ANYWHERE:
        return None
    clean = [_clean(t) for t in tokens]
    for i, word in enumerate(clean):
        if word in ANYWHERE[lang] or word.startswith("qu'est-ce"):
            return "ouverte", i
        if word in CLAUSE_START[lang]:
            previous = tokens[i - 1].rstrip("  ") if i else ""
            if not i or previous.endswith((",", ";", ":")) or clean[i - 1] in LINKS[lang]:
                return "ouverte", i
    if CHOICE[lang] in clean:
        return None
    return "fermee", None


def questions(words: list[dict]) -> list[tuple[int, int]]:
    spans, start, last = [], 0, None
    for i, word in enumerate(words):
        token = word["w"].rstrip("   ")
        if not _bare(token):
            last = i
        if token.endswith(SENTENCE_END):
            if token.endswith("?") and last is not None and last >= start:
                spans.append((start, last))
            start = i + 1
    return spans


def _read(wav: Path) -> tuple:
    with wave.open(str(wav), "rb") as w:
        return w.getparams(), np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")


def _write(wav: Path, params, pcm: np.ndarray) -> None:
    with wave.open(str(wav), "wb") as w:
        w.setparams(params)
        w.writeframes(pcm.astype("<i2").tobytes())


def _points(tier) -> tuple[np.ndarray, np.ndarray]:
    from parselmouth.praat import call

    n = call(tier, "Get number of points")
    times = np.array([call(tier, "Get time from index", i) for i in range(1, n + 1)])
    values = np.array([call(tier, "Get value at index", i) for i in range(1, n + 1)])
    return times, values


def _median(values: np.ndarray) -> float | None:
    return float(np.median(values)) if len(values) >= 3 else None


def _plan(kind_: str, qi: int | None, span: list[dict], times: np.ndarray, st: np.ndarray):
    start, last = span[0]["s"], span[-1]
    inside = lambda a, b: st[(times >= a) & (times <= b)]
    if kind_ == "ouverte":
        word = span[qi]
        if qi == len(span) - 1:
            return None
        peak = _median(inside(word["s"], word["e"]))
        if peak is None or peak >= PEAK_MIN:
            return None
        middle = (word["s"] + word["e"]) / 2
        after = span[qi + 1]["s"]
        target = [(start - 1, 0.0), (max(word["s"] - 0.05, start), 0.0), (middle, PEAK), (after, AFTER_PEAK),
                  (last["s"], 0.0), (last["e"] + 1, 0.0)]
        weight = [(start - 1, 0.0), (start, 0.0), (start + EDGE, 1.0), (last["s"] - TAIL_GUARD, 1.0),
                  (last["s"] - 0.02, 0.0), (last["e"] + 1, 0.0)]
        return target, weight, f"pic ajouté sur « {_clean(word['w'])} »"
    tail = inside(last["s"], last["e"] + 0.1)
    final = _median(tail[-5:]) if len(tail) >= 3 else None
    if final is None or final >= RISE_MIN:
        return None
    rise_from = max(last["s"] + (last["e"] - last["s"]) * 0.35, last["e"] - RISE_SPAN)
    target = [(start - 1, 0.0), (rise_from, 0.0), (last["e"], RISE), (last["e"] + 1, RISE)]
    weight = [(start - 1, 0.0), (start, 0.0), (start + EDGE, 1.0), (last["e"] + 1, 1.0)]
    return target, weight, "montée ajoutée à la fin"


def _curve(points, t: np.ndarray) -> np.ndarray:
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


def adjust(wav: Path, words: list[dict], lang: str) -> list[str]:
    found = []
    for a, b in questions(words):
        span = words[a:b + 1]
        shape = kind([w["w"] for w in span], lang)
        if shape:
            found.append((span, shape))
    if not found:
        return []
    import parselmouth
    from parselmouth.praat import call

    params, pcm = _read(wav)
    rate = params.framerate
    sound = parselmouth.Sound(pcm.astype(np.float64) / 32768.0, sampling_frequency=rate)
    manipulation = call(sound, "To Manipulation", TIME_STEP, FLOOR, CEILING)
    tier = call(manipulation, "Extract pitch tier")
    times, values = _points(tier)
    if len(times) < 3:
        return []
    new = 12 * np.log2(values)
    changes, regions = [], []
    for span, (kind_, qi) in found:
        start, end = span[0]["s"], span[-1]["e"] + 0.1
        mask = (times >= start) & (times <= end)
        if mask.sum() < 5:
            continue
        reference = np.median(values[mask])
        st = 12 * np.log2(values / reference)
        plan = _plan(kind_, qi, span, times, st)
        if not plan:
            continue
        target, weight, label = plan
        w = _curve(weight, times) * mask
        shaped = KEEP * st + _curve(target, times)
        new = np.where(mask, new + w * (shaped - st), new)
        text = " ".join(x["w"] for x in span).replace(" ", " ")
        changes.append(f"« {text} » : {label}")
        regions.append((start - SPLICE_BEFORE, span[-1]["e"] + SPLICE_AFTER))
    if not changes:
        return []
    call(tier, "Remove points between", 0, sound.duration)
    for t, v in zip(times, 2 ** (new / 12)):
        call(tier, "Add point", float(t), float(v))
    call([tier, manipulation], "Replace pitch tier")
    result = call(manipulation, "Get resynthesis (overlap-add)")
    shaped = np.clip(result.values[0] * 32768.0, -32768, 32767)
    shaped = np.pad(shaped, (0, max(0, len(pcm) - len(shaped))))[:len(pcm)]
    out = pcm.astype(np.float64)
    fade = max(1, int(FADE * rate))
    for a, b in regions:
        i, j = max(0, int(a * rate)), min(len(pcm), int(b * rate))
        if j - i <= 2 * fade:
            continue
        ramp = np.ones(j - i)
        ramp[:fade] = np.linspace(0.0, 1.0, fade)
        ramp[-fade:] = np.linspace(1.0, 0.0, fade)
        out[i:j] = out[i:j] * (1 - ramp) + shaped[i:j] * ramp
    _write(wav, params, np.round(out))
    return changes
