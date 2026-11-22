import re

import numpy as np

from ideo import align, fidelity, prosody

FIDELITY_MIN = 0.90
FORMULA_MAX = 0.50
SPEED_RATIO_MIN = 0.85
RISE_TARGET = (7.0, 10.0)
LEVEL_TARGET = (2.0, 5.0)
LAST_WORD_TAIL = 0.08
UNKNOWN_DISTANCE = 10.0
TAKES = 12
VOWELS = "aeiouyàâäéèêëîïôöùûüœ"
TELL_ME = {
    "fr": "Dis-moi", "en": "Tell me", "es": "Dime", "de": "Sag mir", "it": "Dimmi", "nl": "Vertel me",
    "pl": "Powiedz mi", "tr": "Söyle bana",
}
ENDING = re.compile(r"(?P<gap>\s*)(?P<marks>[.?!]+)$")


def _tell_me(lang: str) -> re.Pattern | None:
    opener = TELL_ME.get(lang)
    if not opener:
        return None
    body = r"\s+".join(re.escape(p) for p in opener.split())
    return re.compile(rf"^(?P<open>{body})(?![\w])[ ,.…]*(?P<rest>.+)$", re.IGNORECASE | re.DOTALL)


def _closing(text: str) -> str:
    stripped = text.rstrip()
    match = ENDING.search(stripped)
    if not match:
        return text
    mark = "?!" if "?" in match.group("marks") else "!"
    return stripped[:match.start()] + match.group("gap") + mark + text[len(stripped):]


def shape(text: str, lang: str) -> str:
    pattern = _tell_me(lang)
    match = pattern.match(text.strip()) if pattern else None
    if match and re.search(r"\w", match.group("rest")):
        rest = match.group("rest").strip()
        return f"{match.group('open')} ?! {_closing(rest[:1].upper() + rest[1:])}"
    return _closing(text)


def formula_length(lang: str) -> int:
    opener = TELL_ME.get(lang)
    return len(opener.split()) if opener else 0


def starts_with_formula(text: str, lang: str) -> bool:
    pattern = _tell_me(lang)
    match = pattern.match(text.strip()) if pattern else None
    return bool(match and re.search(r"\w", match.group("rest")))


def syllables(word: str) -> int:
    letters = re.sub(r"[^a-zàâäéèêëîïôöùûüœ]", "", word.lower())
    if not letters:
        return 1
    count = len(re.findall(rf"[{VOWELS}]+", letters))
    if count > 1 and re.search(r"(?<![aeiouyàâäéèêëîïôöùûüœ])(e|es)$", letters):
        count -= 1
    return max(count, 1)


def _span_speed(words: list[dict]) -> float | None:
    if not words:
        return None
    duration = words[-1]["e"] - words[0]["s"]
    if duration <= 0:
        return None
    return sum(syllables(w["w"]) for w in words) / duration


def speed_ratio(words: list[dict], skip: int) -> float | None:
    body = words[skip:]
    if len(body) < 3:
        return None
    tail, rest = _span_speed(body[-2:]), _span_speed(body[:-2])
    if not tail or not rest:
        return None
    return round(tail / rest, 3)


def contour(signal: np.ndarray, rate: int, word: dict) -> tuple[float | None, float | None]:
    track = prosody.pitch_track(signal, rate)
    if len(track) == 0:
        return None, None
    step = prosody.HOP / prosody.SAMPLE_RATE
    centers = np.arange(len(track)) * step + prosody.FRAME / 2 / prosody.SAMPLE_RATE
    end = word["e"] + LAST_WORD_TAIL
    third = (end - word["s"]) / 3
    voiced = track[~np.isnan(track)]
    if third <= 0 or len(voiced) < 3:
        return None, None
    first = track[(centers >= word["s"]) & (centers < word["s"] + third)]
    last = track[(centers > end - third) & (centers <= end)]
    first, last = first[~np.isnan(first)], last[~np.isnan(last)]
    if len(first) < 2 or len(last) < 2:
        return None, None
    rise = 12 * np.log2(np.median(last) / np.median(first))
    level = 12 * np.log2(np.median(last) / np.median(voiced))
    return round(float(rise), 2), round(float(level), 2)


def _gap(value: float | None, target: tuple[float, float]) -> float:
    if value is None:
        return UNKNOWN_DISTANCE
    low, high = target
    return max(low - value, value - high, 0.0)


def distance(scores: dict) -> float:
    return round(_gap(scores.get("rise"), RISE_TARGET) + _gap(scores.get("level"), LEVEL_TARGET), 3)


def evaluate(wav, spoken: str, heard: list[dict], lang: str, expected: str | None = None) -> dict:
    signal, rate = prosody.read_mono(wav)
    words = align.align_words(align.script_words(spoken), heard, len(signal) / rate)
    skip = formula_length(lang) if starts_with_formula(spoken, lang) else 0
    rise, level = contour(signal, rate, words[-1]) if words else (None, None)
    result = {"fidelity": fidelity.similarity(expected if expected is not None else spoken, heard), "formula": None,
              "speed_ratio": None, "rise": rise, "level": level}
    if skip and len(words) > skip:
        result["formula"] = round(words[skip - 1]["e"] - words[0]["s"], 3)
    result["speed_ratio"] = speed_ratio(words, skip)
    return result


def failed(scores: dict) -> list[str]:
    out = []
    if scores["fidelity"] < FIDELITY_MIN:
        out.append("fidélité")
    if scores["formula"] is not None and scores["formula"] > FORMULA_MAX:
        out.append("formule trop longue")
    if scores["speed_ratio"] is not None and scores["speed_ratio"] < SPEED_RATIO_MIN:
        out.append("fin traînante")
    return out


def rank(scores: dict) -> tuple:
    return (-len(failed(scores)), -distance(scores), scores["fidelity"])


def best(takes: list[dict]) -> int:
    return max(range(len(takes)), key=lambda i: (rank(takes[i]["scores"]), -i))
