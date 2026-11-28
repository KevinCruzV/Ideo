import asyncio
import hashlib
import json
import re
import shutil
import tempfile
import time
import wave
from pathlib import Path
from typing import Protocol

import numpy as np

from ideo import (align, common, config, eleven, fidelity, hookvoice, i18n, intonation, lexicon, numbers, pacing,
                   prosody, transcribe)

TICKS = 1e7
LAUNCHER = Path(__file__).with_name("kyutai_launcher.py")
DEFAULT_SEED = 299792458
TAKE = re.compile(r"_t\d{2}$")
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


EDGE_ATTEMPTS = 3


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
            for attempt in range(EDGE_ATTEMPTS):
                words.clear()
                try:
                    asyncio.run(run(mp3))
                    break
                except Exception as err:
                    if attempt == EDGE_ATTEMPTS - 1:
                        raise common.IdeoError(
                            f"la synthèse vocale a échoué (connexion à edge-tts impossible ?) : {err}"
                        ) from err
                    time.sleep(1.0 + attempt)
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
                         padding: float | None = None, seed: int | None = None) -> dict:
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
                [str(python), str(LAUNCHER), str(DEFAULT_SEED if seed is None else seed), str(jsonl), "--out-folder", str(work / "out"), "--only-wav",
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


def derive_seed(key: str, attempt: int, group: str) -> int:
    digest = hashlib.sha256(f"{key}:{attempt}:{group}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % (2 ** 31 - 2) + 1


def get_backend(log: Path | None = None) -> VoiceBackend:
    return EdgeTTSBackend(log)


def choose_backend(lang: str, log: Path | None = None, job: Path | None = None) -> VoiceBackend:
    chosen = config.engine(job)
    if chosen == "elevenlabs":
        return eleven.ElevenLabsBackend(log, job)
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


def spoken_for(text: str, lang: str, local: bool, name: str = "", plain: bool = False) -> tuple[str, list | None]:
    if plain:
        amounts = numbers.normalize(text, lang, amounts_only=True)
        return lexicon.apply(amounts.text, lang), amounts.units
    if name == HOOK:
        text = hookvoice.shape(text, lang)
    normalized = numbers.normalize(text, lang)
    spoken = lexicon.apply(normalized.text, lang) if local else normalized.text
    return spoken, normalized.units


TRAILING_MARKS = re.compile(r"[\s\u00a0]*[,;:.!?…»”\"')\]]+$")


def _with_punctuation(heard: list[dict], text: str, duration: float) -> list[dict]:
    marks = []
    for w in align.align_words(align.script_words(text), heard, duration):
        found = TRAILING_MARKS.search(w["w"])
        if found:
            marks.append((w["e"], found.group(0)))
    if not marks:
        return heard
    out = []
    for w in heard:
        mark = next((m for e, m in marks if abs(w["e"] - e) < 0.02), None)
        written = TRAILING_MARKS.search(w["w"])
        if mark and (not written or ":" in mark and ":" not in written.group(0)):
            w = {**w, "w": TRAILING_MARKS.sub("", w["w"]) + mark}
        out.append(w)
    return out


def finish_segment(wav: Path, text: str, heard: list[dict], spoken: str | None = None, units: list | None = None) -> list[dict]:
    wav = Path(wav)
    with wave.open(str(wav), "rb") as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (pacing.RATE, 1, 2):
            raise common.IdeoError(f"{wav.name} doit être en 48 kHz mono 16 bits : relancez la voix.")
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    marked = _with_punctuation(heard, spoken or text, len(pcm) / pacing.RATE)
    tight, mapping = pacing.tighten(pcm, marked)
    heard = pacing.remap(heard, mapping)
    marked = pacing.remap(marked, mapping)
    tight, spread = pacing.pause_sentences(tight, marked, pacing.QUESTION_GAP if wav.stem == OUTRO else None)
    heard = pacing.remap(heard, spread)
    if len(tight) != len(pcm):
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(pacing.RATE)
            w.writeframes(tight.astype("<i2").tobytes())
    duration = len(tight) / pacing.RATE
    shown = align.script_words(text)
    said = align.script_words(spoken) if spoken and spoken != text else shown
    words = align.align_words(said, heard, duration)
    if units and sum(u["orig"] for u in units) == len(shown) and sum(u["said"] for u in units) == len(said):
        return _regroup(words, shown, units)
    if len(said) == len(shown):
        return [{**w, "w": label} for w, label in zip(words, shown)]
    return align.align_words(shown, heard, duration)


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
    question = part.get("question")
    if isinstance(question, str) and question.strip():
        outro = f"{question.strip()} {outro}"
    segments.append(("seg_99_outro", outro))
    return segments


def segment_tags(part: dict) -> dict:
    tags = {"seg_00_hook": part.get("jeu_hook"), OUTRO: part.get("jeu_question")}
    tags.update({f"seg_{i:02d}": scene.get("jeu") for i, scene in enumerate(part["scenes"], start=1)})
    return {name: tag for name, tag in tags.items() if isinstance(tag, str) and tag in config.TAGS}


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
    chosen = config.engine(job)
    paid = chosen == "elevenlabs"
    local = not paid and lang in KYUTAI_LANGS and chosen == "kyutai" and config.kyutai_installed()
    out_dir = job / "parts" / f"{n:02d}"
    return [name for name, text in segments(plan, part)
            if (out_dir / f"{name}.wav").exists() and (out_dir / f"{name}.words.json").exists()
            and _stored(out_dir, name, text) != spoken_for(text, lang, local, name, plain=paid)[0]]


def _short(err: Exception) -> str:
    text = " ".join(str(err).split())
    return text if len(text) <= REASON_LENGTH else text[:REASON_LENGTH - 1].rstrip() + "…"


def _log_line(log: Path, line: str) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _generate(backend, items: list[tuple[str, str]], lang: str, out_dir: Path, temp: float | None = None,
              key: str = "", attempt: int = 0) -> None:
    if hasattr(backend, "synthesize_batch"):
        edges = [(n, t) for n, t in items if TAKE.sub("", n) in BOUNDARY_SEGMENTS]
        rest = [(n, t) for n, t in items if TAKE.sub("", n) not in BOUNDARY_SEGMENTS]
        if rest:
            backend.synthesize_batch(rest, lang, out_dir, temp=temp, seed=derive_seed(key, attempt, "pass"))
        if edges:
            backend.synthesize_batch(edges, lang, out_dir, temp=max(temp or 0.0, config.kyutai_hook_temp()),
                                     padding=config.kyutai_hook_padding_bonus(), seed=derive_seed(key, attempt, "hook"))
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


def _expand(todo: list[tuple[str, str]], spoken: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for name, _ in todo:
        if name == HOOK:
            out += [(f"{HOOK}_t{i:02d}", spoken[HOOK]) for i in range(hookvoice.TAKES)]
        else:
            out.append((name, spoken[name]))
    return out


def _pick_hook(out_dir: Path, spoken: str, expected: str, lang: str, log: Path) -> tuple[dict, dict]:
    candidates = []
    for i in range(hookvoice.TAKES):
        wav = out_dir / f"{HOOK}_t{i:02d}.wav"
        heard = retranscribe(wav, lang, log)
        candidates.append({"scores": hookvoice.evaluate(wav, spoken, heard, lang, expected), "heard": heard,
                           "prosody": prosody.score(wav), "bytes": wav.read_bytes()})
        wav.unlink()
    index = hookvoice.best(candidates)
    chosen = candidates[index]
    problems = hookvoice.failed(chosen["scores"])
    info = {**chosen["scores"], "passed": not problems, "failed": problems, "takes": hookvoice.TAKES, "chosen": index}
    take = {"fidelity": chosen["scores"]["fidelity"], "prosody": chosen["prosody"], "heard": chosen["heard"],
            "bytes": chosen["bytes"]}
    return take, info


def _settle_local(backend, items: list[tuple[str, str]], lang: str, out_dir: Path, log: Path, key: str = "") -> tuple:
    prepared = {name: spoken_for(text, lang, True, name) for name, text in items}
    spoken = {name: p[0] for name, p in prepared.items()}
    takes: dict = {name: [] for name, _ in items}
    hook_info = None
    redone = 0
    todo = items
    for attempt in range(MAX_REDOS + 1):
        temp = None if attempt == 0 else REDO_TEMPS[min(attempt - 1, len(REDO_TEMPS) - 1)]
        _generate(backend, _expand(todo, spoken), lang, out_dir, temp, key, attempt)
        for name, _ in todo:
            expected = numbers.plain_words(*prepared[name])
            if name == HOOK:
                take, hook_info = _pick_hook(out_dir, spoken[name], expected, lang, log)
                takes[name].append(take)
                continue
            wav = out_dir / f"{name}.wav"
            heard = retranscribe(wav, lang, log)
            takes[name].append({"fidelity": fidelity.similarity(expected, heard), "prosody": prosody.score(wav),
                                "heard": heard, "bytes": wav.read_bytes()})
        todo = [(n, t) for n, t in items if n != HOOK and needs_redo(n, best_take(takes[n]))]
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
            {n: c["prosody"] for n, c in chosen.items() if c["prosody"] is not None}, redone, hook_info)


def _write_json_merged(path: Path, update: dict) -> None:
    current = common.load_json(path) if path.exists() else {}
    current.update(update)
    common.save_json(path, current)


def _kind(backend) -> str:
    if getattr(backend, "local", False):
        return "local"
    return "paid" if getattr(backend, "paid", False) else "edge"


def _fallback_backend(lang: str, log: Path, failed: str = "local"):
    return get_backend(log)


TRIM_TAIL = 0.12
TRIM_FADE = 0.02


def _cut_after(wav: Path, end: float, next_start: float | None) -> bool:
    with wave.open(str(wav), "rb") as w:
        rate, params = w.getframerate(), w.getparams()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    stop = end + TRIM_TAIL
    if next_start is not None:
        stop = min(stop, max(end, (end + next_start) / 2))
    cut = int(stop * rate)
    if cut >= len(pcm):
        return False
    kept = pcm[:cut].astype(np.float64)
    fade = min(int(TRIM_FADE * rate), len(kept))
    if fade:
        kept[-fade:] *= np.linspace(1.0, 0.0, fade)
    with wave.open(str(wav), "wb") as w:
        w.setparams(params)
        w.writeframes(kept.astype("<i2").tobytes())
    return True


OUTRO = "seg_99_outro"
QUESTION_SPLIT = re.compile(r"^(.+?\?)\s+(\S.*)$", re.S)


def _pieces(name: str, text: str) -> list[str]:
    match = QUESTION_SPLIT.match(text) if name == OUTRO else None
    return [match.group(1), match.group(2)] if match else [text]


def _paid_piece(backend, name: str, text: str, lang: str, wav: Path, before, after, log: Path,
                tag: str | None = None) -> tuple[list[dict], float]:
    said = f"[{tag}] {text}" if tag and getattr(backend, "tags", False) else text

    def take():
        words = backend.synthesize(said, lang, wav, previous_text=before, next_text=after)
        listened = retranscribe(wav, lang, log)
        return (words or listened, fidelity.similarity(text, listened), wav.read_bytes(),
                fidelity.added(text, listened), listened)

    words, score, audio, extra, listened = take()
    if score < eleven.RETRY_BELOW or extra:
        reason = f"mot ajouté : {' '.join(extra)}" if extra else f"ressemblance {score:.2f}"
        _log_line(log, f"voix : {name} refait une fois ({reason})")
        words2, score2, audio2, extra2, listened2 = take()
        if (len(extra2), -score2) <= (len(extra), -score):
            words, score, audio, extra, listened = words2, score2, audio2, extra2, listened2
    wav.write_bytes(audio)
    if extra:
        kept = fidelity.keep_count(text, listened)
        if kept and _cut_after(wav, listened[kept - 1]["e"], listened[kept]["s"] if kept < len(listened) else None):
            _log_line(log, f"voix : {name} coupe le mot ajouté en fin : {' '.join(extra)}")
            words = [w for w in words if w["e"] <= listened[kept - 1]["e"] + 0.05] or words
            extra = fidelity.added(text, listened[:kept])
            score = fidelity.similarity(text, listened[:kept])
    if extra:
        _log_line(log, f"voix : {name} garde un mot ajouté : {' '.join(extra)}")
        score = min(score, eleven.ADDED_WORD_SCORE)
    return words, score


JOIN_PAUSE = pacing.QUESTION_GAP


def _join_wavs(paths: list[Path], target: Path) -> list[float]:
    chunks, starts, cursor = [], [], 0.0
    for k, path in enumerate(paths):
        with wave.open(str(path), "rb") as w:
            params = w.getparams()
            data = w.readframes(w.getnframes())
        if k:
            chunks.append(bytes(round(JOIN_PAUSE * params.framerate) * 2 * params.nchannels))
            cursor += JOIN_PAUSE
        starts.append(cursor)
        cursor += len(data) / 2 / params.nchannels / params.framerate
        chunks.append(data)
    with wave.open(str(target), "wb") as w:
        w.setparams(params)
        w.writeframes(b"".join(chunks))
    return starts


def _retouch(wav: Path, words: list[dict], lang: str, name: str, log: Path) -> None:
    try:
        changes = intonation.adjust(wav, words, lang, hook=name == HOOK)
    except ImportError:
        _log_line(log, f"voix : {name} intonation non retouchée (praat-parselmouth absent)")
        return
    except (RuntimeError, ValueError) as err:
        _log_line(log, f"voix : {name} intonation non retouchée ({err})")
        return
    for change in changes:
        _log_line(log, f"voix : {name} intonation retouchée, {change}")


def _settle_paid(backend, pending: list[tuple[str, str]], items: list[tuple[str, str]], lang: str, out_dir: Path,
                 log: Path, tags: dict | None = None) -> tuple[dict, dict]:
    tags = tags or {}
    order = [name for name, _ in items]
    spoken = {name: spoken_for(text, lang, False, name, plain=True)[0] for name, text in items}
    heard_by_name: dict = {}
    scores: dict = {}
    for name, _ in pending:
        index = order.index(name)
        before = spoken[order[index - 1]] if index else None
        after = spoken[order[index + 1]] if index + 1 < len(order) else None
        wav = out_dir / f"{name}.wav"
        pieces = _pieces(name, spoken[name])
        if len(pieces) == 1:
            words, score = _paid_piece(backend, name, pieces[0], lang, wav, before, after, log, tags.get(name))
        else:
            work = out_dir / f"{name}.pieces"
            parts = [work / str(k) / f"{name}.wav" for k in range(len(pieces))]
            for path in parts:
                path.parent.mkdir(parents=True, exist_ok=True)
            results = [_paid_piece(backend, name, piece, lang, path, before if k == 0 else None,
                                   pieces[1] if k == 0 else after, log, tags.get(name) if k == 0 else None)
                       for k, (piece, path) in enumerate(zip(pieces, parts))]
            starts = _join_wavs(parts, wav)
            shutil.rmtree(work)
            words = [{**w, "s": w["s"] + at, "e": w["e"] + at} for (ws, _), at in zip(results, starts) for w in ws]
            score = min(sc for _, sc in results)
        _retouch(wav, words, lang, name, log)
        heard_by_name[name] = words
        scores[name] = score
        (out_dir / f"{name}.spoken.txt").write_text(spoken[name], encoding="utf-8")
    return heard_by_name, scores


def _run_backend(backend, pending, items, lang, out_dir, log, key, tags=None) -> dict:
    kind = _kind(backend)
    result = {"heard": {}, "scores": {}, "pitch": {}, "hook": None}
    if kind == "local":
        heard, scores, pitch, _, hook_info = _settle_local(backend, pending, lang, out_dir, log, key)
        result.update(heard=heard, scores=scores, pitch=pitch, hook=hook_info)
    elif kind == "paid":
        heard, scores = _settle_paid(backend, pending, items, lang, out_dir, log, tags)
        result.update(heard=heard, scores=scores)
    else:
        for name, text in pending:
            wav = out_dir / f"{name}.wav"
            spoken, _ = spoken_for(text, lang, False, name)
            heard = backend.synthesize(spoken, lang, wav)
            result["heard"][name] = heard if heard else retranscribe(wav, lang, log)
            (out_dir / f"{name}.spoken.txt").write_text(spoken, encoding="utf-8")
    return result


PAID_LIMIT = 600


def paid_guard(job: Path, n: int, pending: list[tuple[str, str]], lang: str, pay: bool) -> None:
    if pay or not pending or config.paid_characters(job) <= 0:
        return
    total = sum(len(spoken_for(text, lang, False, name, plain=True)[0]) for name, text in pending)
    if total > PAID_LIMIT:
        raise common.IdeoError(f"la voix payante de cette vidéo est déjà faite : refaire {len(pending)} phrase(s) de la partie {n} "
                               f"coûterait environ {total} caractères ElevenLabs. Relance produce avec --payer pour confirmer.")


def _segment_done(out_dir: Path, name: str, text: str, lang: str, kind: str) -> bool:
    if not ((out_dir / f"{name}.wav").exists() and (out_dir / f"{name}.words.json").exists()):
        return False
    return _stored(out_dir, name, text) == spoken_for(text, lang, kind == "local", name, plain=kind == "paid")[0]


def _kind_for(job: Path, lang: str) -> str:
    chosen = config.engine(job)
    if chosen == "elevenlabs":
        return "paid"
    return "local" if lang in KYUTAI_LANGS and chosen == "kyutai" and config.kyutai_installed() else "edge"


def done_segments(job: Path, plan: dict, part: dict) -> list[str]:
    lang = plan["lang"]
    out_dir = Path(job) / "parts" / f"{part['n']:02d}"
    kind = _kind_for(Path(job), lang)
    return [name for name, text in segments(plan, part) if _segment_done(out_dir, name, text, lang, kind)]


def guard_redo(job: Path, n: int, pay: bool, keep: bool) -> None:
    job = Path(job)
    if config.engine(job) != "elevenlabs":
        return
    plan = common.load_json(job / "plan.json")
    part = next((p for p in plan["parts"] if p["n"] == n), None)
    if part is None:
        return
    done = set(done_segments(job, plan, part)) if keep else set()
    pending = [(name, text) for name, text in segments(plan, part) if name not in done]
    paid_guard(job, n, pending, plan["lang"], pay)


def voice_part(job: Path, n: int, backend: VoiceBackend | None = None, pay: bool = False) -> list[Path]:
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
    backend = backend or choose_backend(lang, log, job)
    items = segments(plan, part)
    paths = [out_dir / f"{name}.wav" for name, _ in items]
    kind = _kind(backend)

    pending = [(name, text) for name, text in items if not _segment_done(out_dir, name, text, lang, kind)]
    if kind == "paid":
        paid_guard(job, n, pending, lang, pay)
    try:
        if pending:
            fallback = None
            key = f"{job.name}:{n}"
            try:
                result = _run_backend(backend, pending, items, lang, out_dir, log, key, segment_tags(part))
            except common.IdeoError as err:
                if kind == "edge":
                    raise
                fallback = _short(err)
                _log_line(log, f"voix : repli ({err})")
                backend = _fallback_backend(lang, log, kind)
                result = _run_backend(backend, pending, items, lang, out_dir, log, key)
            kind = _kind(backend)
            for name, text in pending:
                wav = out_dir / f"{name}.wav"
                spoken, units = spoken_for(text, lang, kind == "local", name, plain=kind == "paid")
                common.save_json(out_dir / f"{name}.words.json",
                                 finish_segment(wav, text, result["heard"][name], spoken, units))
            info = {"engine": {"local": "kyutai", "paid": "elevenlabs", "edge": "edge"}[kind], "fallback": fallback,
                    "local_missing": config.local_voice_missing(lang)}
            if kind == "paid":
                previous = read_info(out_dir)
                before = previous.get("characters", 0) if previous.get("engine") == "elevenlabs" else 0
                info["characters"] = before + backend.characters
                config.add_paid_characters(job, backend.characters)
                _log_line(log, f"voix : ElevenLabs, {backend.characters} caractères envoyés ({info['characters']} pour la partie)")
            common.save_json(out_dir / "voice-info.json", info)
            if kind != "local":
                _forget_local_scores(out_dir, [name for name, _ in pending])
            if result["hook"]:
                common.save_json(out_dir / "voice-hook.json", result["hook"])
            if result["scores"]:
                _write_json_merged(out_dir / "voice-quality.json", result["scores"])
            if result["pitch"]:
                _write_json_merged(out_dir / "voice-prosody.json", result["pitch"])
    except common.IdeoError as err:
        common.mark(job, step, False, str(err))
        raise
    except Exception as err:
        common.mark(job, step, False, str(err))
        raise common.IdeoError(f"la voix a échoué : {err}") from err
    if kind == "local" and (out_dir / "voice-info.json").exists():
        _backfill_prosody(out_dir, [name for name, _ in items])
    common.mark(job, step, True, f"{len(paths)} segments")
    return paths


def _forget_local_scores(out_dir: Path, names: list[str]) -> None:
    if HOOK in names:
        (out_dir / "voice-hook.json").unlink(missing_ok=True)
    path = out_dir / "voice-prosody.json"
    if not path.exists():
        return
    try:
        kept = {k: v for k, v in common.load_json(path).items() if k not in names}
    except (OSError, ValueError, AttributeError):
        kept = {}
    if kept:
        common.save_json(path, kept)
    else:
        path.unlink()


def read_info(out_dir: Path) -> dict:
    path = out_dir / "voice-info.json"
    try:
        data = common.load_json(path) if path.exists() else {}
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


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
