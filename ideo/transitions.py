from functools import lru_cache
from pathlib import Path

import numpy as np

from ideo import config, music

RATE = 48000
FPS = 30
WIPE_BEFORE = 7
WIPE_FRAMES = 9
VARIANTS = 4
TAIL = 0.14
BANDS = 9
DUCK_DB = 6.0
ACTIVE = 0.1


def _frame(seconds: float) -> int:
    return round(round(seconds * FPS, 6))


def _bandpass(noise: np.ndarray, low: float, high: float) -> np.ndarray:
    spectrum = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(len(noise), 1 / RATE)
    spectrum[(freqs < low) | (freqs > high)] = 0
    return np.fft.irfft(spectrum, len(noise))


def _envelope(length: int) -> np.ndarray:
    t = np.arange(length) / RATE
    peak = WIPE_BEFORE / FPS
    rise = np.clip(t / peak, 0, 1) ** 2
    fall = np.exp(-np.clip(t - peak, 0, None) / 0.07)
    env = np.where(t <= peak, rise, fall)
    edge = int(0.012 * RATE)
    env[:edge] *= np.linspace(0, 1, edge)
    env[-edge:] *= np.linspace(1, 0, edge)
    return env


def _normalize(sound: np.ndarray) -> np.ndarray:
    active = np.abs(sound) > ACTIVE * np.max(np.abs(sound))
    rms = float(np.sqrt(np.mean(sound[active] ** 2)))
    return (sound / rms).astype(np.float32)


def _whoosh(seed: int, rising: bool) -> np.ndarray:
    rng = np.random.RandomState(seed)
    length = int((WIPE_FRAMES / FPS + TAIL) * RATE)
    duration = length / RATE
    noise = rng.standard_normal(length)
    centers = np.geomspace(320, 3800, BANDS)
    t = np.arange(length) / RATE
    out = np.zeros(length)
    for k, center in enumerate(centers):
        order = k if rising else BANDS - 1 - k
        peak = 0.06 + order / (BANDS - 1) * 0.55 * duration
        gain = np.exp(-(((t - peak) / (0.16 * duration)) ** 2))
        out += gain * _bandpass(noise, center * 0.6, center * 1.5)
    return _normalize(out * _envelope(length))


def _rustle(seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    length = int((WIPE_FRAMES / FPS + TAIL) * RATE)
    noise = _bandpass(rng.standard_normal(length), 2500, 9000)
    flutter = np.convolve(np.abs(rng.standard_normal(length)), np.ones(int(0.004 * RATE)) / int(0.004 * RATE), mode="same")
    clicks = np.zeros(length)
    clicks[rng.randint(0, length, 14)] = rng.uniform(1.5, 3.0, 14)
    clicks = np.convolve(clicks, np.hanning(int(0.003 * RATE)), mode="same")
    body = noise * (0.35 + flutter) + _bandpass(rng.standard_normal(length), 600, 1800) * 0.25 * flutter
    return _normalize((body + clicks * noise.std()) * _envelope(length))


@lru_cache(maxsize=1)
def variants() -> tuple:
    return (_whoosh(11, True), _rustle(23), _whoosh(37, False), _rustle(41))


def _spans(offsets: list[dict]) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    voice = [(o["start"], o["end"]) for o in offsets]
    clips = [(o["clip"]["start"], o["clip"]["end"]) for o in offsets if o.get("clip")]
    return voice, clips


def _overlap(a: tuple[float, float], spans: list[tuple[float, float]]) -> bool:
    return any(a[0] < e and a[1] > s for s, e in spans)


def mix(raw: Path, offsets: list[dict]) -> dict:
    info = {"enabled": config.transition_sfx_enabled(), "count": 0, "skipped": 0, "ducked": 0}
    if not info["enabled"] or len(offsets) < 2:
        return info
    samples = music.read_wav(raw)
    voice, clips = _spans(offsets)
    pieces = [samples[int(s * RATE):int(e * RATE)] for s, e in voice if int(e * RATE) > int(s * RATE)]
    speech = np.concatenate(pieces) if pieces else samples
    reference = float(np.sqrt(np.mean(speech ** 2))) if len(speech) else 0.0
    if reference <= 0:
        return info
    level = 10 ** (config.transition_sfx_db() / 20) * reference
    relative = []
    for i in range(1, len(offsets)):
        first = _frame(offsets[i]["start"]) - WIPE_BEFORE
        if first < 0:
            continue
        begin = first / FPS
        window = (begin, begin + WIPE_FRAMES / FPS)
        if _overlap(window, clips):
            info["skipped"] += 1
            continue
        ducked = _overlap((begin, begin + WIPE_BEFORE / FPS), voice)
        gain = level * (10 ** (-DUCK_DB / 20) if ducked else 1.0)
        sound = variants()[(i - 1) % VARIANTS] * gain
        start = int(begin * RATE)
        end = min(start + len(sound), len(samples))
        if end <= start:
            continue
        samples[start:end] += sound[:end - start]
        info["count"] += 1
        info["ducked"] += 1 if ducked else 0
        relative.append(20 * np.log10(gain / reference))
    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    if peak > 0.98:
        samples = samples * (0.98 / peak)
    music.write_wav(raw, samples)
    info["mean_db"] = round(float(np.mean(relative)), 1) if relative else None
    return info
