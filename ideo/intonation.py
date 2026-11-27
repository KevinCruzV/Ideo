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

PEAK_GOAL = 7.0
RISE_GOAL = 7.0
PEAK_MIN = 5.0
RISE_MIN = 5.0
MAX_SHIFT = 6.0
MIN_SHIFT = 1.5
RISE_SPAN = 0.25
RAMP = 0.05
OUTLIER = 5.0
SPLICE = 0.08
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
    last = span[-1]
    inside = lambda a, b: st[(times >= a) & (times <= b)]
    if kind_ == "ouverte":
        if qi == len(span) - 1:
            return None
        word = span[qi]
        peak = _median(inside(word["s"], word["e"]))
        if peak is None or peak >= PEAK_MIN:
            return None
        shift = min(PEAK_GOAL - peak, MAX_SHIFT)
        if shift < MIN_SHIFT:
            return None
        follow = span[qi + 1]
        fade_end = min((follow["s"] + follow["e"]) / 2, last["s"])
        bump = [(word["s"] - RAMP, 0.0), (word["s"] + 0.02, shift), (word["e"], shift), (max(fade_end, word["e"] + 0.02), 0.0)]
        region = (word["s"] - SPLICE, max(fade_end, word["e"] + 0.02) + SPLICE)
        return bump, region, f"pic ajouté sur « {_clean(word['w'])} » (+{shift:.1f} demi-tons)"
    tail = inside(last["s"], last["e"] + 0.1)
    final = _median(tail[-5:]) if len(tail) >= 3 else None
    if final is None or final >= RISE_MIN:
        return None
    shift = min(RISE_GOAL - final, MAX_SHIFT)
    if shift < MIN_SHIFT:
        return None
    rise_from = max(last["s"] + (last["e"] - last["s"]) * 0.35, last["e"] - RISE_SPAN)
    bump = [(rise_from, 0.0), (last["e"], shift), (last["e"] + 0.1, shift)]
    region = (rise_from - SPLICE, last["e"] + 0.1 + SPLICE)
    return bump, region, f"montée ajoutée à la fin (+{shift:.1f} demi-tons)"


def _outliers(st: np.ndarray) -> np.ndarray:
    padded = np.pad(st, 2, mode="edge")
    local = np.array([np.median(padded[i:i + 5]) for i in range(len(st))])
    return np.abs(st - local) > OUTLIER


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
    changes, regions = [], []
    shift = np.zeros(len(times))
    for span, (kind_, qi) in found:
        mask = (times >= span[0]["s"]) & (times <= span[-1]["e"] + 0.1)
        if mask.sum() < 5:
            continue
        st = 12 * np.log2(values / np.median(values[mask]))
        plan = _plan(kind_, qi, span, times, st)
        if not plan:
            continue
        bump, region, label = plan
        xs, ys = zip(*bump)
        shift += np.interp(times, xs, ys, left=0.0, right=0.0)
        text = " ".join(x["w"] for x in span).replace("\u00a0", " ")
        changes.append(f"« {text} » : {label}")
        regions.append(region)
    if not changes:
        return []
    keep = ~_outliers(12 * np.log2(values))
    call(tier, "Remove points between", 0, sound.duration)
    for t, v, s_ in zip(times[keep], values[keep], shift[keep]):
        call(tier, "Add point", float(t), float(v * 2 ** (s_ / 12)))
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
