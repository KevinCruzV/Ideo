import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000
FRAME = 640
HOP = 160
FMIN = 80.0
FMAX = 450.0
THRESHOLD = 0.15
ENERGY_GATE = 0.05
MIN_VOICED = 12
SCALE = 1.044
FLAT = 2.0
BOUNDARY = 2.4


def read_mono(path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        rate = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
        if w.getnchannels() > 1:
            data = data.reshape(-1, w.getnchannels()).mean(axis=1)
    return data, rate


def _resample(signal: np.ndarray, rate: int) -> np.ndarray:
    if rate == SAMPLE_RATE:
        return signal
    factor = rate / SAMPLE_RATE
    positions = np.arange(0, len(signal) - 1, factor)
    return np.interp(positions, np.arange(len(signal)), signal)


def pitch_track(signal: np.ndarray, rate: int) -> np.ndarray:
    x = _resample(signal, rate)
    if len(x) < FRAME * 2:
        return np.array([])
    count = 1 + (len(x) - FRAME) // HOP
    index = np.arange(FRAME)[None, :] + HOP * np.arange(count)[:, None]
    frames = x[index]
    frames = frames - frames.mean(axis=1, keepdims=True)
    energy = np.sqrt((frames ** 2).mean(axis=1))
    lo, hi = int(SAMPLE_RATE / FMAX), int(SAMPLE_RATE / FMIN)
    spectrum = np.fft.rfft(frames, n=2 * FRAME, axis=1)
    acf = np.fft.irfft(spectrum * np.conj(spectrum), axis=1)[:, :hi + 2]
    squares = np.cumsum(frames ** 2, axis=1)
    total = squares[:, -1][:, None]
    taus = np.arange(1, hi + 2)
    tail = total - squares[:, taus - 1]
    lead = squares[:, FRAME - taus - 1]
    diff = lead + tail - 2 * acf[:, taus]
    cumulative = np.cumsum(diff, axis=1)
    norm = diff * taus[None, :] / np.maximum(cumulative, 1e-12)
    window = norm[:, lo - 1:hi]
    below = window < THRESHOLD
    first = np.argmax(below, axis=1)
    found = below.any(axis=1)
    best = np.argmin(window, axis=1)
    pick = np.where(found, first, best)
    tau = pick + lo
    voiced = (found | (window[np.arange(count), best] < 0.25)) & (energy > ENERGY_GATE * energy.max())
    prev = np.clip(tau - 1, lo, hi)
    nxt = np.clip(tau + 1, lo, hi)
    y0 = norm[np.arange(count), prev - 1]
    y1 = norm[np.arange(count), tau - 1]
    y2 = norm[np.arange(count), nxt - 1]
    denom = y0 - 2 * y1 + y2
    with np.errstate(divide="ignore", invalid="ignore"):
        shift = np.where(np.abs(denom) > 1e-9, 0.5 * (y0 - y2) / denom, 0.0)
    refined = tau + np.clip(shift, -1, 1)
    f0 = SAMPLE_RATE / refined
    return np.where(voiced, f0, np.nan)


def _clean(track: np.ndarray) -> np.ndarray:
    voiced = track[~np.isnan(track)]
    if len(voiced) < 3:
        return voiced
    kernel = 5
    padded = np.pad(voiced, kernel // 2, mode="edge")
    smooth = np.array([np.median(padded[i:i + kernel]) for i in range(len(voiced))])
    return smooth


def score_signal(signal: np.ndarray, rate: int) -> float | None:
    track = _clean(pitch_track(signal, rate))
    if len(track) < MIN_VOICED:
        return None
    semitones = 12 * np.log2(track / np.median(track))
    keep = np.abs(semitones) < 12
    if keep.sum() < MIN_VOICED:
        return None
    return round(float(np.std(semitones[keep])) * SCALE, 3)


def score(path) -> float | None:
    signal, rate = read_mono(path)
    return score_signal(signal, rate)


def median(values: list) -> float | None:
    clean = sorted(v for v in values if isinstance(v, (int, float)))
    return round(float(np.median(clean)), 2) if clean else None
