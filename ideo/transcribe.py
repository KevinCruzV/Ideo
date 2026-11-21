import wave
from pathlib import Path

import numpy as np

from ideo import common

MIN_WORDS = 150


def read_pcm(wav_path) -> np.ndarray:
    with wave.open(str(wav_path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0


def transcribe(job: Path, model: str = "small", min_words: int = MIN_WORDS) -> list[dict]:
    job = Path(job)
    words_path = job / "words.json"
    lang_path = job / "lang.txt"
    step = common.read_status(job)["steps"].get("transcribe")
    if step and step["ok"] and words_path.exists() and lang_path.exists():
        return common.load_json(words_path)
    try:
        from faster_whisper import WhisperModel

        whisper = WhisperModel(model, device="cpu", compute_type="int8")
        segments, info = whisper.transcribe(read_pcm(job / "source.wav"), word_timestamps=True, vad_filter=True)
        words = [
            {"w": word.word.strip(), "s": round(word.start, 2), "e": round(word.end, 2)}
            for seg in segments
            for word in (seg.words or [])
        ]
        if len(words) < min_words:
            raise common.IdeoError(
                f"pas assez de parole : {len(words)} mots détectés, il en faut au moins {min_words}"
            )
    except common.IdeoError as err:
        common.mark(job, "transcribe", False, str(err))
        raise
    except Exception as err:
        common.mark(job, "transcribe", False, str(err))
        raise common.IdeoError(f"la transcription a échoué : {err}") from err
    common.save_json(words_path, words)
    lang_path.write_text(info.language, encoding="utf-8")
    common.mark(job, "transcribe", True, f"{len(words)} mots, langue {info.language}")
    return words
