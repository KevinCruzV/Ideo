import asyncio
import json
import shutil
import tempfile
import wave
from pathlib import Path
from typing import Protocol

import numpy as np

from ideo import align, common, config, fidelity, hookvoice, i18n, lexicon, numbers, pacing, prosody, transcribe

TICKS = 1e7
KYUTAI_LANGS = config.KYUTAI_LANGS
KEEP_THRESHOLD = 0.90
ALERT_THRESHOLD = 0.80
MAX_REDOS = 3
REDO_TEMPS = (0.75, 0.9, 1.0)
HOOK = "seg_00_hook"
BOUNDARY_SEGMENTS = (HOOK, "seg_99_outro")
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

    def synthesize_batch(self, items: list[tuple[str, str]], lang: str, out_dir: Path, temp: float | None = None,
                         padding: float | None = None) -> dict:
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
                 "--padding-bonus", f"{config.kyutai_padding_bonus() if padding is None else padding:g}"] + ([] if temp is None else ["--temp", f"{temp:g}"]),
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
    if lang in KYUTAI_LANGS and config.engine() == "kyutai" and config.kyutai_installed():
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


def spoken_for(text: str, lang: str, local: bool, name: str = "") -> tuple[str, list | None]:
    if name == HOOK:
        text = hookvoice.shape(text, lang)
    normalized = numbers.normalize(text, lang)
    spoken = lexicon.apply(normalized.text, lang) if local else normalized.text
    return spoken, normalized.units


def finish_segment(wav: Path, text: str, heard: list[dict], spoken: str | None = None, units: list | None = None) -> list[dict]:
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
    shown = align.script_words(text)
    said = align.script_words(spoken) if spoken and spoken != text else shown
    words = align.align_words(said, pacing.remap(heard, mapping), duration)
    if units and sum(u["orig"] for u in units) == len(shown) and sum(u["said"] for u in units) == len(said):
        return _regroup(words, shown, units)
    if len(said) == len(shown):
        return [{**w, "w": label} for w, label in zip(words, shown)]
    return align.align_words(shown, pacing.remap(heard, mapping), duration)


def _regroup(words: list[dict], shown: list[str], units: list) -> list[dict]:
    out, k, o = [], 0, 0
    for unit in units:
        chunk = words[k:k + unit["said"]]
        k += unit["said"]
        start, end, count = chunk[0]["s"], chunk[-1]["e"], unit["orig"]
        for j in range(count):
            out.append({"w": shown[o + j], "s": round(start + (end - start) * j / count, 3),
                        "e": round(start + (end - start) * (j + 1) / count, 3)})
        o += count
    return out


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


def _stored(out_dir: Path, name: str, text: str) -> str:
    sidecar = out_dir / f"{name}.spoken.txt"
    return sidecar.read_text(encoding="utf-8") if sidecar.exists() else text


def stale(job: Path, n: int) -> list[str]:
    job = Path(job)
    plan = common.load_json(job / "plan.json")
    part = next((p for p in plan["parts"] if p["n"] == n), None)
    if part is None:
        return []
    lang = plan["lang"]
    local = lang in KYUTAI_LANGS and config.engine() == "kyutai" and config.kyutai_installed()
    out_dir = job / "parts" / f"{n:02d}"
    return [name for name, text in segments(plan, part)
            if (out_dir / f"{name}.wav").exists() and (out_dir / f"{name}.words.json").exists()
            and _stored(out_dir, name, text) != spoken_for(text, lang, local, name)[0]]


def _short(err: Exception) -> str:
    text = " ".join(str(err).split())
    return text if len(text) <= REASON_LENGTH else text[:REASON_LENGTH - 1].rstrip() + "…"


def _log_line(log: Path, line: str) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _generate(backend, items: list[tuple[str, str]], lang: str, out_dir: Path, temp: float | None = None) -> None:
    if hasattr(backend, "synthesize_batch"):
        edges = [(n, t) for n, t in items if n in BOUNDARY_SEGMENTS]
        rest = [(n, t) for n, t in items if n not in BOUNDARY_SEGMENTS]
        if rest:
            backend.synthesize_batch(rest, lang, out_dir, temp=temp)
        if edges:
            backend.synthesize_batch(edges, lang, out_dir, temp=max(temp or 0.0, config.kyutai_hook_temp()),
                                     padding=config.kyutai_hook_padding_bonus())
        return
    for name, text in items:
        backend.synthesize(text, lang, out_dir / f"{name}.wav")


def target_for(name: str) -> float:
    return prosody.BOUNDARY if name in BOUNDARY_SEGMENTS else prosody.FLAT


def _faithful(take: dict) -> bool:
    return take["fidelity"] >= KEEP_THRESHOLD


def best_take(takes: list[dict]) -> dict:
    lively = lambda t: t["prosody"] if t["prosody"] is not None else float("inf")
    faithful = [t for t in takes if _faithful(t)]
    if faithful:
        return max(faithful, key=lively)
    return max(takes, key=lambda t: (t["fidelity"], lively(t)))


def needs_redo(name: str, take: dict) -> bool:
    if not _faithful(take):
        return True
    return take["prosody"] is not None and take["prosody"] < target_for(name)


def _settle_local(backend, items: list[tuple[str, str]], lang: str, out_dir: Path, log: Path) -> tuple[dict, dict, dict, int]:
    prepared = {name: spoken_for(text, lang, True, name) for name, text in items}
    spoken = {name: p[0] for name, p in prepared.items()}
    takes: dict = {name: [] for name, _ in items}
    redone = 0
    todo = items
    for attempt in range(MAX_REDOS + 1):
        temp = None if attempt == 0 else REDO_TEMPS[min(attempt - 1, len(REDO_TEMPS) - 1)]
        _generate(backend, [(name, spoken[name]) for name, _ in todo], lang, out_dir, temp)
        for name, _ in todo:
            wav = out_dir / f"{name}.wav"
            heard = retranscribe(wav, lang, log)
            takes[name].append({"fidelity": fidelity.similarity(numbers.plain_words(*prepared[name]), heard), "prosody": prosody.score(wav),
                                "heard": heard, "bytes": wav.read_bytes()})
        todo = [(n, t) for n, t in items if needs_redo(n, best_take(takes[n]))]
        if not todo or attempt == MAX_REDOS:
            break
        redone += len(todo)
    chosen = {name: best_take(takes[name]) for name, _ in items}
    for name, _ in items:
        (out_dir / f"{name}.wav").write_bytes(chosen[name]["bytes"])
        (out_dir / f"{name}.spoken.txt").write_text(spoken[name], encoding="utf-8")
    scores = [c["prosody"] for c in chosen.values() if c["prosody"] is not None]
    _log_line(log, f"voix : segments refaits : {redone}, ressemblance la plus basse : "
                   f"{min(c['fidelity'] for c in chosen.values()):.2f}, intonation médiane : "
                   f"{prosody.median(scores) if scores else 'inconnue'}")
    return ({n: c["heard"] for n, c in chosen.items()}, {n: c["fidelity"] for n, c in chosen.items()},
            {n: c["prosody"] for n, c in chosen.items() if c["prosody"] is not None}, redone)


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
    local = getattr(backend, "local", False)

    def done(name: str, text: str) -> bool:
        if not ((out_dir / f"{name}.wav").exists() and (out_dir / f"{name}.words.json").exists()):
            return False
        return _stored(out_dir, name, text) == spoken_for(text, lang, local, name)[0]

    pending = [(name, text) for name, text in items if not done(name, text)]
    try:
        if pending:
            fallback = None
            heard_by_name: dict = {}
            scores: dict = {}
            pitch: dict = {}
            if local:
                try:
                    heard_by_name, scores, pitch, _ = _settle_local(backend, pending, lang, out_dir, log)
                except common.IdeoError as err:
                    fallback = _short(err)
                    _log_line(log, f"voix : repli sur la voix en ligne ({err})")
                    backend = get_backend(log)
            if fallback or not getattr(backend, "local", False):
                for name, text in pending:
                    wav = out_dir / f"{name}.wav"
                    spoken, _ = spoken_for(text, lang, False, name)
                    heard = backend.synthesize(spoken, lang, wav)
                    heard_by_name[name] = heard if heard else retranscribe(wav, lang, log)
                    (out_dir / f"{name}.spoken.txt").write_text(spoken, encoding="utf-8")
            engine_is_local = getattr(backend, "local", False)
            for name, text in pending:
                wav = out_dir / f"{name}.wav"
                spoken, units = spoken_for(text, lang, engine_is_local, name)
                common.save_json(out_dir / f"{name}.words.json",
                                 finish_segment(wav, text, heard_by_name[name], spoken, units))
            engine = "kyutai" if getattr(backend, "local", False) else "edge"
            common.save_json(out_dir / "voice-info.json", {"engine": engine, "fallback": fallback,
                                                           "local_missing": config.local_voice_missing(lang)})
            if scores:
                _write_json_merged(out_dir / "voice-quality.json", scores)
                _write_json_merged(out_dir / "voice-prosody.json", pitch)
    except common.IdeoError as err:
        common.mark(job, step, False, str(err))
        raise
    except Exception as err:
        common.mark(job, step, False, str(err))
        raise common.IdeoError(f"la voix a échoué : {err}") from err
    if local and (out_dir / "voice-info.json").exists():
        _backfill_prosody(out_dir, [name for name, _ in items])
    common.mark(job, step, True, f"{len(paths)} segments")
    return paths


def _backfill_prosody(out_dir: Path, names: list[str]) -> None:
    path = out_dir / "voice-prosody.json"
    known = common.load_json(path) if path.exists() else {}
    missing = {}
    for name in names:
        wav = out_dir / f"{name}.wav"
        if name not in known and wav.exists():
            score = prosody.score(wav)
            if score is not None:
                missing[name] = score
    if missing:
        _write_json_merged(path, missing)
