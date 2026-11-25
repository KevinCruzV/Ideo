import wave

import numpy as np

from ideo import common


def rms_db_per_second(wav_path) -> np.ndarray:
    with wave.open(str(wav_path), "rb") as w:
        rate = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    seconds = int(np.ceil(len(pcm) / rate))
    out = np.empty(seconds, dtype=np.float64)
    for i in range(seconds):
        chunk = pcm[i * rate:(i + 1) * rate]
        out[i] = 20 * np.log10(float(np.sqrt(np.mean(chunk ** 2))) + 1e-9)
    return out


MAX_SFX = 10.0
BRIDGE = 1
STRONG_DB = 6
WEAK_DB = 3


def _runs(rms_db: np.ndarray, first: int, last: int, weak: float, strong: float) -> list[tuple[int, int]]:
    runs: list[list] = []
    begin = None
    peak = False
    for sec in range(first, last + 1):
        on = sec < last and rms_db[sec] > weak
        if on:
            if begin is None:
                begin, peak = sec, False
            peak = peak or rms_db[sec] > strong
        elif begin is not None:
            runs.append([begin, sec, peak])
            begin = None
    merged: list[list] = []
    for run in runs:
        if merged and run[0] - merged[-1][1] <= BRIDGE:
            merged[-1][1] = run[1]
            merged[-1][2] = merged[-1][2] or run[2]
        else:
            merged.append(run)
    return [(r[0], r[1]) for r in merged if r[2]]


def find_sfx(rms_db: np.ndarray, words: list[dict], min_len: float = 0.8) -> list[dict]:
    if len(rms_db) == 0:
        return []
    median = float(np.median(rms_db))
    strong, weak = median + STRONG_DB, median + WEAK_DB
    total = float(len(rms_db))
    bounds = [0.0] + [edge for w in words for edge in (w["s"], w["e"])] + [total]
    gaps = [(bounds[i], bounds[i + 1]) for i in range(0, len(bounds), 2)]
    found = []
    for gap_start, gap_end in gaps:
        if gap_end - gap_start < min_len:
            continue
        first = int(gap_start)
        last = min(int(np.ceil(gap_end)), len(rms_db))
        for begin, end in _runs(rms_db, first, last, weak, strong):
            start, stop = max(gap_start, float(begin)), min(gap_end, float(end))
            stop = min(stop, start + MAX_SFX)
            if stop - start >= min_len:
                found.append({"at": common.fmt_ts(start), "s": round(start, 2), "e": round(stop, 2)})
    return found
