import asyncio
import shutil
import tempfile
import wave
from pathlib import Path
from typing import Protocol

import numpy as np

from ideo import align, common, i18n, pacing, transcribe

EDGE_RATE = "+6%"
TICKS = 1e7

EDGE_VOICES = {
    "fr": "fr-FR-HenriNeural",
    "en": "en-US-GuyNeural",
    "es": "es-ES-AlvaroNeural",
    "de": "de-DE-ChristophNeural",
    "it": "it-IT-DiegoNeural",
    "pt": "pt-BR-AntonioNeural",
    "nl": "nl-NL-MaartenNeural",
    "pl": "pl-PL-MarekNeural",
    "tr": "tr-TR-AhmetNeural",
}


def unsupported(lang: str) -> str | None:
    if lang in EDGE_VOICES:
        return None
    return (f"la langue de la vidéo (« {lang} ») n'a pas de voix de synthèse. "
            f"Langues possibles : {', '.join(EDGE_VOICES)}. Les langues qui ne s'écrivent pas en alphabet latin "
            f"ne sont pas encore prises en charge. Choisis une vidéo dans l'une de ces langues.")


class VoiceBackend(Protocol):
    def synthesize(self, text: str, lang: str, out_wav: Path) -> list[dict] | None: ...


def _ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise common.IdeoError("ffmpeg est introuvable : installez-le (par exemple avec brew install ffmpeg).")
    return path


class EdgeTTSBackend:
    def __init__(self, log: Path | None = None):
        self.log = log

    def synthesize(self, text: str, lang: str, out_wav: Path) -> list[dict] | None:
        voice = EDGE_VOICES.get(lang)
        if not voice:
            raise common.IdeoError(unsupported(lang))
        import edge_tts

        out_wav = Path(out_wav)
        words: list[dict] = []

        async def run(mp3: Path) -> None:
            communicate = edge_tts.Communicate(text, voice, rate=EDGE_RATE, boundary="WordBoundary")
            with mp3.open("wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        start = chunk["offset"] / TICKS
                        words.append({"w": chunk["text"], "s": round(start, 4),
                                  "e": round(start + chunk["duration"] / TICKS, 4)})

        with tempfile.TemporaryDirectory() as tmp:
            mp3 = Path(tmp) / "voice.mp3"
            try:
                asyncio.run(run(mp3))
            except Exception as err:
                raise common.IdeoError(
                    f"la synthèse vocale a échoué (connexion à edge-tts impossible ?) : {err}"
                ) from err
            if not mp3.exists() or mp3.stat().st_size == 0:
                raise common.IdeoError("la synthèse vocale a échoué : aucun audio reçu")
            common.run(
                [_ffmpeg(), "-y", "-i", str(mp3), "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(out_wav)],
                self.log or out_wav.parent / "ffmpeg.log",
            )
        return words or None


def get_backend(log: Path | None = None) -> VoiceBackend:
    return EdgeTTSBackend(log)


def retranscribe(wav: Path, lang: str, log: Path | None = None) -> list[dict]:
    wav = Path(wav)
    with tempfile.TemporaryDirectory() as tmp:
        wav16 = Path(tmp) / "seg16.wav"
        common.run(
            [_ffmpeg(), "-y", "-i", str(wav), "-ac", "1", "-ar", "16000", str(wav16)], log or wav.parent / "ffmpeg.log"
        )
        words, _ = transcribe.whisper_words(transcribe.read_pcm(wav16), language=lang)
    return words


def finish_segment(wav: Path, text: str, heard: list[dict]) -> list[dict]:
    wav = Path(wav)
    with wave.open(str(wav), "rb") as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (pacing.RATE, 1, 2):
            raise common.IdeoError(f"{wav.name} doit être en 48 kHz mono 16 bits : relancez la voix.")
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    tight, mapping = pacing.tighten(pcm)
    if len(tight) != len(pcm):
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(pacing.RATE)
            w.writeframes(tight.astype("<i2").tobytes())
    duration = len(tight) / pacing.RATE
    return align.align_words(align.script_words(text), pacing.remap(heard, mapping), duration)


def segments(plan: dict, part: dict) -> list[tuple[str, str]]:
    lang = plan["lang"]
    parts = plan["parts"]
    index = parts.index(part)
    if len(parts) == 1:
        outro = i18n.t("outro_single", lang)
    elif index + 1 < len(parts):
        nxt = parts[index + 1]
        outro = i18n.t("outro_next", lang, n=nxt["n"], title=nxt["title"])
    else:
        outro = i18n.t("outro_last", lang)
    segments = [("seg_00_hook", part["hook"])]
    segments += [(f"seg_{i:02d}", scene["say"]) for i, scene in enumerate(part["scenes"], start=1)]
    segments.append(("seg_99_outro", outro))
    return segments


def voice_part(job: Path, n: int, backend: VoiceBackend | None = None) -> list[Path]:
    job = Path(job)
    plan = common.load_json(job / "plan.json")
    part = next((p for p in plan["parts"] if p["n"] == n), None)
    if part is None:
        raise common.IdeoError(f"partie {n} introuvable dans plan.json")
    lang = plan["lang"]
    step = f"voice-{n:02d}"
    out_dir = job / "parts" / f"{n:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = job / "logs" / f"voice-{n:02d}.log"
    backend = backend or get_backend(log)
    paths = []
    try:
        for name, text in segments(plan, part):
            wav = out_dir / f"{name}.wav"
            words_path = out_dir / f"{name}.words.json"
            paths.append(wav)
            if wav.exists() and words_path.exists():
                continue
            heard = backend.synthesize(text, lang, wav)
            if not heard:
                heard = retranscribe(wav, lang, log)
            common.save_json(words_path, finish_segment(wav, text, heard))
    except common.IdeoError as err:
        common.mark(job, step, False, str(err))
        raise
    except Exception as err:
        common.mark(job, step, False, str(err))
        raise common.IdeoError(f"la voix a échoué : {err}") from err
    common.mark(job, step, True, f"{len(paths)} segments")
    return paths
