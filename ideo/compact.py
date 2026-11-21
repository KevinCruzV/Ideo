import re
from pathlib import Path

from ideo import common, sfx as sfx_mod

PAUSE = 1.2
MAX_WORDS = 60
SPONSOR_SPAN = 60.0
SPONSOR_GAP = 2.0
SPONSOR_WORDS = (
    "sponsorisé par", "sponsorisée par", "code promo",
    "sponsored by", "today's sponsor", "this video is brought to you by", "thanks to our sponsor",
)
SPONSOR_NEGATIONS = (
    "pas sponsoris", "non sponsoris", "jamais sponsoris", "aucun sponsor", "pas de sponsor", "pas de code promo",
    "not sponsored", "n't sponsored", "no sponsor", "not a sponsor",
)


def header(info: dict) -> list[str]:
    lines = [
        f"Titre : {info.get('title', '')}",
        f"Chaîne : {info.get('channel', '')}",
        f"Durée : {common.fmt_ts(info.get('duration') or 0)}",
        f"Langue : {info.get('language') or 'inconnue'}",
    ]
    chapters = info.get("chapters") or []
    if chapters:
        lines.append("Chapitres :")
        lines += [f"- {common.fmt_ts(c['start_time'])} {c['title']}" for c in chapters]
    return lines


def paragraphs(words: list[dict], breaks: list[float] = ()) -> list[dict]:
    out, current, previous_end = [], [], None
    pending = sorted(breaks)

    def flush():
        if current:
            out.append({"s": current[0]["s"], "e": current[-1]["e"], "text": " ".join(w["w"] for w in current)})
            current.clear()

    for word in words:
        cut = bool(pending) and pending[0] < word["s"]
        while pending and pending[0] < word["s"]:
            pending.pop(0)
        if current and (cut or len(current) >= MAX_WORDS or word["s"] - previous_end >= PAUSE):
            flush()
        current.append(word)
        previous_end = word["e"]
    flush()
    return out


def is_sponsor_text(text: str) -> bool:
    low = re.sub(r"\s+(['’])", r"\1", text.lower()).replace("’", "'")
    low = " ".join(low.split())
    if any(phrase in low for phrase in SPONSOR_NEGATIONS):
        return False
    return any(phrase in low for phrase in SPONSOR_WORDS)


def _inside(para: dict, segments: list[dict]) -> bool:
    length = para["e"] - para["s"]
    if length <= 0:
        return any(seg["s"] <= para["s"] < seg["e"] for seg in segments)
    covered = sum(max(0.0, min(para["e"], seg["e"]) - max(para["s"], seg["s"])) for seg in segments)
    return covered / length > 0.5


def _ranges(paras: list[dict], flags: list[bool], probable: bool) -> list[dict]:
    out, previous = [], False
    for para, flag in zip(paras, flags):
        if flag and previous:
            out[-1]["e"] = max(out[-1]["e"], para["e"])
        elif flag:
            out.append({"s": para["s"], "e": para["e"], "probable": probable})
        previous = flag
    return out


def hidden_ranges(paras: list[dict], info: dict) -> list[dict]:
    segments = [s for s in info.get("skip") or [] if isinstance(s, dict) and "s" in s and "e" in s]
    if segments:
        return _ranges(paras, [_inside(p, segments) for p in paras], False)
    flags = [False] * len(paras)
    for i, para in enumerate(paras):
        if is_sponsor_text(para["text"]):
            flags[i] = True
            for j in range(i + 1, len(paras)):
                if paras[j]["s"] >= para["s"] + SPONSOR_SPAN or paras[j]["s"] - paras[j - 1]["e"] >= SPONSOR_GAP:
                    break
                flags[j] = True
    return _ranges(paras, flags, True)


def build(words: list[dict], sfx: list[dict], info: dict) -> tuple[str, list[dict]]:
    paras = paragraphs(words, [m["s"] for m in sfx])
    hidden = hidden_ranges(paras, info)

    def hidden_at(t: float):
        return next((r for r in hidden if r["s"] <= t <= r["e"]), None)

    events = [(p["s"], 1, p) for p in paras] + [(m["s"], 0, m) for m in sfx]
    body, done = [], set()
    for _, order, item in sorted(events, key=lambda e: (e[0], e[1])):
        r = hidden_at(item["s"])
        if r is not None:
            if id(r) not in done:
                done.add(id(r))
                label = "passage probablement sponsorisé" if r["probable"] else "passage sponsorisé"
                body.append(f"[{label} {common.fmt_ts(r['s'])} à {common.fmt_ts(r['e'])}, ignoré]")
            continue
        if order == 0:
            body.append(f"[son {common.fmt_ts(item['s'])} {item['e'] - item['s']:.1f}s]")
        else:
            body.append(f"[{common.fmt_ts(item['s'])}] {item['text']}")
    text = "\n".join(header(info)) + "\n\n" + "\n".join(body) + "\n"
    return text, [{"s": round(r["s"], 2), "e": round(r["e"], 2), "probable": r["probable"]} for r in hidden]


def compact(words: list[dict], sfx: list[dict], info: dict) -> str:
    return build(words, sfx, info)[0]


def prepare_transcript(job: Path) -> dict:
    job = Path(job)
    out = job / "transcript_compact.md"
    sfx_path = job / "sfx.json"
    skip_path = job / "skip.json"
    lang = (job / "lang.txt").read_text(encoding="utf-8").strip()
    words = common.load_json(job / "words.json")
    step = common.read_status(job)["steps"].get("transcript")
    if step and step["ok"] and out.exists() and sfx_path.exists() and skip_path.exists():
        markers = common.load_json(sfx_path)
        text = out.read_text(encoding="utf-8")
    else:
        info = {**common.load_json(job / "info.json"), "language": lang}
        rms = sfx_mod.rms_db_per_second(job / "source.wav")
        markers = sfx_mod.find_sfx(rms, words)
        text, hidden = build(words, markers, info)
        segments = [s for s in info.get("skip") or [] if isinstance(s, dict)]
        common.save_json(sfx_path, markers)
        common.save_json(skip_path, {"hidden": hidden, "segments": segments})
        out.write_text(text, encoding="utf-8")
        common.mark(job, "transcript", True, f"{len(words)} mots, {len(markers)} repères de sons")
    paragraphs_count = sum(1 for line in text.splitlines() if re.match(r"^\[\d", line))
    return {"words": len(words), "paragraphs": paragraphs_count, "sfx": len(markers), "lang": lang}
