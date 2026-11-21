import math
import re
from pathlib import Path

from ideo import align, common, i18n, textmatch, voice

FPS = 30
WIDTH = 1080
HEIGHT = 1920
PAUSE = 0.5
MAX_GROUP = 4
FIRST_ITEM_FRAMES = 9
UNCAPPED = frozenset({"object-state"})
FINAL_PUNCT = (".", "!", "?", "…", ";", ":")
APOSTROPHES = re.compile("['’‘ʼ`´]")


def _frame(seconds: float, fps: int = FPS) -> int:
    return round(round(seconds * fps, 6))


def _word_index(words: list[dict], anchor: str) -> int | None:
    span = textmatch.find_span([w["w"] for w in words], anchor)
    if span is not None:
        return span[0]
    tokens, owner = [], []
    for i, w in enumerate(words):
        for part in APOSTROPHES.split(w["w"]):
            if part:
                tokens.append(part)
                owner.append(i)
    needle = APOSTROPHES.sub(" ", anchor)
    span = textmatch.find_span(tokens, needle)
    if span is not None:
        return owner[span[0]]
    return None


def anchor_frame(seg_words: list[dict], anchor: str, seg_start: float, seg_dur: float, say: str,
                 fps: int = FPS) -> int:
    anchor = textmatch.anchor_text(anchor) or ""
    index = _word_index(seg_words, anchor) if seg_words and anchor else None
    if index is not None:
        return _frame(seg_start + seg_words[index]["s"], fps)
    pos = say.lower().find(anchor.lower())
    ratio = pos / len(say) if pos >= 0 and say else 0.0
    return _frame(seg_start + ratio * seg_dur, fps)


def _runs(words: list[dict]) -> list[list[dict]]:
    runs, current = [], []
    for i, w in enumerate(words):
        current.append(w)
        last = i == len(words) - 1
        if last or w["w"].rstrip().endswith(FINAL_PUNCT) or words[i + 1]["s"] - w["e"] > PAUSE:
            runs.append(current)
            current = []
    return runs


def _split_run(run: list[dict]) -> list[list[dict]]:
    count = math.ceil(len(run) / MAX_GROUP)
    base, extra = divmod(len(run), count)
    out, pos = [], 0
    for k in range(count):
        size = base + (1 if k < extra else 0)
        out.append(run[pos:pos + size])
        pos += size
    return out


def caption_groups(words: list[dict], fps: int = FPS) -> list[dict]:
    groups = []
    for run in _runs(words):
        for chunk in _split_run(run):
            items = []
            for i, w in enumerate(chunk):
                start = _frame(w["s"], fps)
                items.append({"w": w["w"], "from": start})
            for i, item in enumerate(items):
                if i + 1 < len(items):
                    end = items[i + 1]["from"]
                else:
                    end = _frame(chunk[-1]["e"], fps)
                item["to"] = max(end, item["from"] + 1) if i + 1 == len(items) else end
            groups.append({"words": items, "from": items[0]["from"], "to": items[-1]["to"]})
    for a, b in zip(groups, groups[1:]):
        if a["to"] > b["from"]:
            a["to"] = max(b["from"], a["from"])
            a["words"][-1]["to"] = max(min(a["words"][-1]["to"], a["to"]), a["words"][-1]["from"])
    return groups


def _shift(words: list[dict], offset: float) -> list[dict]:
    return [{"w": w["w"], "s": w["s"] + offset, "e": w["e"] + offset} for w in words]


def build_timeline(job: Path, n: int, total: int) -> Path:
    job = Path(job)
    step = f"timeline-{n:02d}"
    try:
        path = _build(job, n, total)
    except common.IdeoError as err:
        common.mark(job, step, False, str(err))
        raise
    except Exception as err:
        common.mark(job, step, False, str(err))
        raise common.IdeoError(f"la timeline a échoué : {err}") from err
    common.mark(job, step, True)
    return path


def _build(job: Path, n: int, total: int) -> Path:
    plan = common.load_json(job / "plan.json")
    part = next((p for p in plan["parts"] if p["n"] == n), None)
    if part is None:
        raise common.IdeoError(f"partie {n} introuvable dans plan.json")
    lang = plan["lang"]
    out_dir = job / "parts" / f"{n:02d}"
    offsets_path = out_dir / "offsets.json"
    if not offsets_path.exists():
        raise common.IdeoError(f"offsets.json est introuvable : assemblez d'abord l'audio de la partie {n}.")
    offsets = common.load_json(offsets_path)
    texts = dict(voice.segments(plan, part))
    scenes = {f"seg_{i:02d}": scene for i, scene in enumerate(part["scenes"], start=1)}
    source_words = common.load_json(job / "words.json") if (job / "words.json").exists() else []

    expected = list(texts)
    if [o["seg"] for o in offsets] != expected:
        raise common.IdeoError("offsets.json ne correspond plus au plan : relancez l'assemblage audio.")

    duration_sec = offsets[-1]["end"]
    frames = math.ceil(round(duration_sec * FPS, 6))
    starts = [_frame(o["start"]) for o in offsets]
    starts[0] = 0
    ends = starts[1:] + [frames]

    segments = []
    captions = []
    for entry, begin, finish in zip(offsets, starts, ends):
        name = entry["seg"]
        words_path = out_dir / f"{name}.words.json"
        if not words_path.exists():
            raise common.IdeoError(f"{name}.words.json est introuvable : relancez la voix de la partie {n}.")
        seg_words = common.load_json(words_path)
        seg_dur = entry["end"] - entry["start"]
        captions.extend(caption_groups(_shift(seg_words, entry["start"])))
        clip = entry["clip"]
        if clip and clip["kind"] == "quote":
            inside = [w for w in source_words if w["s"] >= clip["src_start"] - 1e-6 and w["e"] <= clip["src_end"] + 1e-6]
            relative = _shift(inside, -clip["src_start"])
            written = align.align_words(align.script_words(scenes[name]["props"]["text"]), relative,
                                        clip["end"] - clip["start"])
            captions.extend(caption_groups(_shift(written, clip["start"])))
        if name == "seg_00_hook":
            segments.append({"kind": "hook", "from": begin, "to": finish, "props": {"text": texts[name]}, "items": []})
        elif name == "seg_99_outro":
            segments.append({"kind": "outro", "from": begin, "to": finish, "props": {"text": texts[name]}})
        else:
            scene = scenes[name]
            items = []
            for item in scene.get("items", []):
                at = anchor_frame(seg_words, item["on"], entry["start"], seg_dur, scene["say"])
                at = min(max(at, begin), max(finish - 1, begin))
                if not items and scene["type"] not in UNCAPPED:
                    at = min(at, begin + FIRST_ITEM_FRAMES)
                items.append({"el": item["el"], "at": at})
            segments.append({"kind": "scene", "type": scene["type"], "from": begin, "to": finish,
                             "props": scene.get("props", {}), "items": items})

    timeline = {
        "fps": FPS,
        "width": WIDTH,
        "height": HEIGHT,
        "durationInFrames": frames,
        "lang": lang,
        "audio": "part.wav",
        "watermark": "Ideo",
        "chapter": {"part": n, "total": total, "title": part["title"], "label": i18n.t("part_label", lang)},
        "segments": segments,
        "captions": captions,
    }
    path = out_dir / "timeline.json"
    common.save_json(path, timeline)
    return path
