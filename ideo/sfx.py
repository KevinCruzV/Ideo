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


def find_sfx(rms_db: np.ndarray, words: list[dict], min_len: float = 0.8) -> list[dict]:
    if len(rms_db) == 0:
        return []
    threshold = float(np.median(rms_db)) + 6
    total = float(len(rms_db))
    bounds = [0.0] + [edge for w in words for edge in (w["s"], w["e"])] + [total]
    gaps = [(bounds[i], bounds[i + 1]) for i in range(0, len(bounds), 2)]
    found = []
    for gap_start, gap_end in gaps:
        if gap_end - gap_start < min_len:
            continue
        first = int(gap_start)
        last = min(int(np.ceil(gap_end)), len(rms_db))
        run = None
        for sec in range(first, last + 1):
            loud = sec < last and rms_db[sec] > threshold
            if loud and run is None:
                run = sec
            elif not loud and run is not None:
                start, end = max(gap_start, float(run)), min(gap_end, float(sec))
                if end - start >= min_len:
                    found.append({"at": common.fmt_ts(start), "s": round(start, 2), "e": round(end, 2)})
                run = None
    return found
