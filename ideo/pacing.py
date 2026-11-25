from typing import Callable

import numpy as np

RATE = 48000
FRAME = 480
THRESHOLD_DB = -32.0
EDGE_DB = -50.0
KEEP_EDGE = 0.03
LONG_PAUSE = 0.60
PAUSE = 0.50
SENTENCE_GAP = 0.30
SENTENCE_END = (".", "!", "?", "…")
CLOSERS = "»”\"')]"
MIN_LETTERS = 3
BREATH_TAIL = 0.15
BREATH_LEAD = 0.08
BREATH_MIN_GAP = 0.25
BREATH_FADE = 0.01
FRAGMENT_DB = -60.0
FRAGMENT_MAX = 0.25
FRAGMENT_GAP = 0.20


def _loud(pcm: np.ndarray, db: float = THRESHOLD_DB) -> np.ndarray:
    count = -(-len(pcm) // FRAME)
    padded = np.zeros(count * FRAME, dtype=np.float64)
    padded[:len(pcm)] = pcm
    rms = np.sqrt((padded.reshape(count, FRAME) ** 2).mean(axis=1))
    return rms > 32768.0 * 10 ** (db / 20)


def _cuts(pcm: np.ndarray) -> list[tuple[int, int]]:
    loud = _loud(pcm)
    if not loud.any():
        return []
    edge = _loud(pcm, EDGE_DB)
    first = min(int(np.argmax(loud)), int(np.argmax(edge)))
    last_loud = len(loud) - 1 - int(np.argmax(loud[::-1]))
    last = max(last_loud, len(edge) - 1 - int(np.argmax(edge[::-1])))
    keep = round(KEEP_EDGE * RATE)
    start = max(0, first * FRAME - keep)
    end = min(len(pcm), (last + 1) * FRAME + keep)
    cuts = []
    if start > 0:
        cuts.append((0, start))
    side = round(PAUSE * RATE / 2)
    long_run = round(LONG_PAUSE * RATE)
    i = first
    while i <= last_loud:
        if loud[i]:
            i += 1
            continue
        j = i
        while not loud[j]:
            j += 1
        a, b = i * FRAME, j * FRAME
        if b - a > long_run:
            cuts.append((a + side, b - side))
        i = j
    if end < len(pcm):
        cuts.append((end, len(pcm)))
    return cuts


def tighten(pcm: np.ndarray) -> tuple[np.ndarray, Callable[[float], float]]:
    cuts = _cuts(pcm)
    if not cuts:
        return pcm, lambda t: t
    parts, cursor = [], 0
    for a, b in cuts:
        parts.append(pcm[cursor:a])
        cursor = b
    parts.append(pcm[cursor:])
    out = np.concatenate(parts)

    def mapping(t: float) -> float:
        x = t * RATE
        removed = 0
        for a, b in cuts:
            if x >= b:
                removed += b - a
            elif x > a:
                removed += x - a
                break
            else:
                break
        return max(0.0, (x - removed) / RATE)

    return out, mapping


def remap(words: list[dict], mapping: Callable[[float], float]) -> list[dict]:
    return [{"w": w["w"], "s": mapping(w["s"]), "e": mapping(w["e"])} for w in words]


def _ends_sentence(word: str) -> bool:
    text = word.rstrip(CLOSERS)
    return text.endswith(SENTENCE_END) and sum(c.isalpha() for c in text) >= MIN_LETTERS


def pause_sentences(pcm: np.ndarray, words: list[dict]) -> tuple[np.ndarray, Callable[[float], float]]:
    inserts: list[tuple[int, int]] = []
    for word, after in zip(words, words[1:]):
        gap = after["s"] - word["e"]
        if not _ends_sentence(word["w"]) or not 0 <= gap < SENTENCE_GAP:
            continue
        at = word["e"] + (gap / 2 if gap > 0.02 else 0.0)
        inserts.append((min(len(pcm), round(at * RATE)), round((SENTENCE_GAP - gap) * RATE)))
    if not inserts:
        return pcm, lambda t: t
    parts, cursor = [], 0
    for at, length in inserts:
        parts += [pcm[cursor:at], np.zeros(length, dtype=pcm.dtype)]
        cursor = at
    parts.append(pcm[cursor:])

    def mapping(t: float) -> float:
        x = t * RATE
        return (x + sum(length for at, length in inserts if x >= at)) / RATE

    return np.concatenate(parts), mapping


def drop_tail_fragment(pcm: np.ndarray) -> np.ndarray:
    sound = _loud(pcm, FRAGMENT_DB)
    if not sound.any():
        return pcm
    last = len(sound) - 1 - int(np.argmax(sound[::-1]))
    longest = round(FRAGMENT_MAX * RATE / FRAME)
    needed = round(FRAGMENT_GAP * RATE / FRAME)
    i = last
    while True:
        while i > 0 and sound[i - 1]:
            i -= 1
        gap_end = i
        while i > 0 and not sound[i - 1]:
            i -= 1
        if i == 0 or last + 1 - gap_end > longest:
            return pcm
        if gap_end - i >= needed:
            break
    out = pcm.copy()
    out[gap_end * FRAME:] = 0
    return out


def gate_breaths(pcm: np.ndarray, words: list[dict]) -> np.ndarray:
    if not words or not len(pcm):
        return pcm
    tail, lead = round(BREATH_TAIL * RATE), round(BREATH_LEAD * RATE)
    fade = round(BREATH_FADE * RATE)
    spans = [(0, round(words[0]["s"] * RATE) - lead)]
    for word, after in zip(words, words[1:]):
        if after["s"] - word["e"] >= BREATH_MIN_GAP:
            spans.append((round(word["e"] * RATE) + tail, round(after["s"] * RATE) - lead))
    spans.append((round(words[-1]["e"] * RATE) + tail, len(pcm)))
    out = pcm.copy()
    for a, b in spans:
        a, b = max(0, a), min(len(pcm), b)
        if b - a <= 2 * fade:
            continue
        out[a:b] = 0
        if a > 0:
            out[a:a + fade] = (pcm[a:a + fade] * np.linspace(1.0, 0.0, fade)).astype(pcm.dtype)
        if b < len(pcm):
            out[b - fade:b] = (pcm[b - fade:b] * np.linspace(0.0, 1.0, fade)).astype(pcm.dtype)
    return out
