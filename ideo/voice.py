import asyncio
import json
import shutil
import tempfile
import wave
from pathlib import Path
from typing import Protocol

import numpy as np

from ideo import align, common, config, fidelity, i18n, pacing, transcribe

TICKS = 1e7
KYUTAI_LANGS = ("fr", "en")
KEEP_THRESHOLD = 0.90
ALERT_THRESHOLD = 0.80
MAX_REDOS = 3
REASON_LENGTH = 90

EDGE_VOICES = {
    "fr": "fr-FR-RemyMultilingualNeural",
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
        if lang not in EDGE_VOICES:
            raise common.IdeoError(unsupported(lang))
        voice = config.voice_for(lang)
        rate = config.rate()
        import edge_tts

        out_wav = Path(out_wav)
        words: list[dict] = []

        async def run(mp3: Path) -> None:
            communicate = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
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


class KyutaiBackend:
    local = True

    def __init__(self, log: Path | None = None):
        self.log = log

    def synthesize_batch(self, items: list[tuple[str, str]], lang: str, out_dir: Path) -> dict:
        python = config.KYUTAI_PYTHON
        if not Path(python).exists():
            raise common.IdeoError("le moteur de voix local est introuvable : lance « python -m ideo setup-voix » "
                                   "ou mets « engine »: « edge » dans config.json.")
        out_dir = Path(out_dir)
        log = self.log or out_dir / "kyutai.log"
        voice = config.kyutai_voice()
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            jsonl = work / "script.jsonl"
            jsonl.write_text("\n".join(json.dumps({"id": name, "turns": [text], "voices": [voice]}, ensure_ascii=False)
                                       for name, text in items) + "\n", encoding="utf-8")
            common.run(
                [str(python), "-m", "moshi_mlx.run_tts", str(jsonl), "--out-folder", str(work / "out"), "--only-wav",
                 "--padding-bonus", f"{config.kyutai_padding_bonus():g}"],
                log,
            )
            for name, _ in items:
                raw = work / "out" / f"{name}.wav"
                if not raw.exists() or raw.stat().st_size == 0:
                    raise common.IdeoError(f"le moteur de voix local n'a pas produit {name}.wav. Voir {log}")
                common.run(
                    [_ffmpeg(), "-y", "-i", str(raw), "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le",
                     str(out_dir / f"{name}.wav")],
                    log,
                )
        return {name: None for name, _ in items}

    def synthesize(self, text: str, lang: str, out_wav: Path) -> list[dict] | None:
        out_wav = Path(out_wav)
        self.synthesize_batch([(out_wav.stem, text)], lang, out_wav.parent)
        return None


def get_backend(log: Path | None = None) -> VoiceBackend:
    return EdgeTTSBackend(log)


def choose_backend(lang: str, log: Path | None = None) -> VoiceBackend:
    if lang in KYUTAI_LANGS and config.engine() == "kyutai":
        return KyutaiBackend(log)
    return get_backend(log)


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


def _short(err: Exception) -> str:
    text = " ".join(str(err).split())
    return text if len(text) <= REASON_LENGTH else text[:REASON_LENGTH - 1].rstrip() + "…"


def _log_line(log: Path, line: str) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _generate(backend, items: list[tuple[str, str]], lang: str, out_dir: Path) -> None:
    if hasattr(backend, "synthesize_batch"):
        backend.synthesize_batch(items, lang, out_dir)
        return
    for name, text in items:
        backend.synthesize(text, lang, out_dir / f"{name}.wav")


def _settle_local(backend, items: list[tuple[str, str]], lang: str, out_dir: Path, log: Path) -> tuple[dict, dict, int]:
    best: dict = {}
    redone = 0
    todo = items
    for attempt in range(MAX_REDOS + 1):
        _generate(backend, todo, lang, out_dir)
        for name, text in todo:
            wav = out_dir / f"{name}.wav"
            heard = retranscribe(wav, lang, log)
            score = fidelity.similarity(text, heard)
            if name not in best or score > best[name][0]:
                best[name] = (score, heard, wav.read_bytes())
        todo = [(n, t) for n, t in items if best[n][0] < KEEP_THRESHOLD]
        if not todo or attempt == MAX_REDOS:
            break
        redone += len(todo)
    for name, _ in items:
        (out_dir / f"{name}.wav").write_bytes(best[name][2])
    _log_line(log, f"voix : segments refaits : {redone}, ressemblance la plus basse : "
                   f"{min(b[0] for b in best.values()):.2f}")
    return {n: b[1] for n, b in best.items()}, {n: b[0] for n, b in best.items()}, redone


def _write_json_merged(path: Path, update: dict) -> None:
    current = common.load_json(path) if path.exists() else {}
    current.update(update)
    common.save_json(path, current)


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
    backend = backend or choose_backend(lang, log)
    items = segments(plan, part)
    paths = [out_dir / f"{name}.wav" for name, _ in items]
    pending = [(name, text) for name, text in items
               if not ((out_dir / f"{name}.wav").exists() and (out_dir / f"{name}.words.json").exists())]
    try:
        if pending:
            fallback = None
            heard_by_name: dict = {}
            scores: dict = {}
            if getattr(backend, "local", False):
                try:
                    heard_by_name, scores, _ = _settle_local(backend, pending, lang, out_dir, log)
                except common.IdeoError as err:
                    fallback = _short(err)
                    _log_line(log, f"voix : repli sur la voix en ligne ({err})")
                    backend = get_backend(log)
            if fallback or not getattr(backend, "local", False):
                for name, text in pending:
                    wav = out_dir / f"{name}.wav"
                    heard = backend.synthesize(text, lang, wav)
                    heard_by_name[name] = heard if heard else retranscribe(wav, lang, log)
            for name, text in pending:
                wav = out_dir / f"{name}.wav"
                common.save_json(out_dir / f"{name}.words.json", finish_segment(wav, text, heard_by_name[name]))
            engine = "kyutai" if getattr(backend, "local", False) else "edge"
            common.save_json(out_dir / "voice-info.json", {"engine": engine, "fallback": fallback})
            if scores:
                _write_json_merged(out_dir / "voice-quality.json", scores)
    except common.IdeoError as err:
        common.mark(job, step, False, str(err))
        raise
    except Exception as err:
        common.mark(job, step, False, str(err))
        raise common.IdeoError(f"la voix a échoué : {err}") from err
    common.mark(job, step, True, f"{len(paths)} segments")
    return paths
