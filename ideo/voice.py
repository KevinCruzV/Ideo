import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Protocol

from ideo import common, i18n, transcribe

EDGE_VOICES = {
    "fr": "fr-FR-HenriNeural",
    "en": "en-US-GuyNeural",
    "es": "es-ES-AlvaroNeural",
    "de": "de-DE-ConradNeural",
    "it": "it-IT-DiegoNeural",
    "pt": "pt-BR-AntonioNeural",
}


class VoiceBackend(Protocol):
    def synthesize(self, text: str, lang: str, out_wav: Path) -> None: ...


def _ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise common.IdeoError("ffmpeg est introuvable : installez-le (par exemple avec brew install ffmpeg).")
    return path


class EdgeTTSBackend:
    def synthesize(self, text: str, lang: str, out_wav: Path) -> None:
        voice = EDGE_VOICES.get(lang)
        if not voice:
            raise common.IdeoError(f"pas de voix pour {lang}")
        import edge_tts

        out_wav = Path(out_wav)
        with tempfile.TemporaryDirectory() as tmp:
            mp3 = Path(tmp) / "voice.mp3"
            try:
                asyncio.run(edge_tts.Communicate(text, voice).save(str(mp3)))
            except Exception as err:
                raise common.IdeoError(
                    f"la synthèse vocale a échoué (connexion à edge-tts impossible ?) : {err}"
                ) from err
            if not mp3.exists() or mp3.stat().st_size == 0:
                raise common.IdeoError("la synthèse vocale a échoué : aucun audio reçu")
            common.run(
                [_ffmpeg(), "-y", "-i", str(mp3), "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(out_wav)],
                Path(tmp) / "ffmpeg.log",
            )


def get_backend() -> VoiceBackend:
    return EdgeTTSBackend()


def retranscribe(wav: Path, lang: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        wav16 = Path(tmp) / "seg16.wav"
        common.run(
            [_ffmpeg(), "-y", "-i", str(wav), "-ac", "1", "-ar", "16000", str(wav16)], Path(tmp) / "ffmpeg.log"
        )
        words, _ = transcribe.whisper_words(transcribe.read_pcm(wav16), language=lang)
    return words


def _segments(plan: dict, part: dict) -> list[tuple[str, str]]:
    lang = plan["lang"]
    parts = plan["parts"]
    index = parts.index(part)
    if index + 1 < len(parts):
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
    backend = backend or get_backend()
    paths = []
    try:
        for name, text in _segments(plan, part):
            wav = out_dir / f"{name}.wav"
            words_path = out_dir / f"{name}.words.json"
            paths.append(wav)
            if wav.exists() and words_path.exists():
                continue
            backend.synthesize(text, lang, wav)
            common.save_json(words_path, retranscribe(wav, lang))
    except common.IdeoError as err:
        common.mark(job, step, False, str(err))
        raise
    except Exception as err:
        common.mark(job, step, False, str(err))
        raise common.IdeoError(f"la voix a échoué : {err}") from err
    common.mark(job, step, True, f"{len(paths)} segments")
    return paths
