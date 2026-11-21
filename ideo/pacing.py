from typing import Callable

import numpy as np

RATE = 48000
FRAME = 480
THRESHOLD_DB = -32.0
KEEP_EDGE = 0.03
LONG_PAUSE = 0.40
PAUSE = 0.35


def _loud(pcm: np.ndarray) -> np.ndarray:
    count = -(-len(pcm) // FRAME)
    padded = np.zeros(count * FRAME, dtype=np.float64)
    padded[:len(pcm)] = pcm
    rms = np.sqrt((padded.reshape(count, FRAME) ** 2).mean(axis=1))
    return rms > 32768.0 * 10 ** (THRESHOLD_DB / 20)


def _cuts(pcm: np.ndarray) -> list[tuple[int, int]]:
    loud = _loud(pcm)
    if not loud.any():
        return []
    first = int(np.argmax(loud))
    last = len(loud) - 1 - int(np.argmax(loud[::-1]))
    keep = round(KEEP_EDGE * RATE)
    start = max(0, first * FRAME - keep)
    end = min(len(pcm), (last + 1) * FRAME + keep)
    cuts = []
    if start > 0:
        cuts.append((0, start))
    side = round(PAUSE * RATE / 2)
    long_run = round(LONG_PAUSE * RATE)
    i = first
    while i <= last:
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
