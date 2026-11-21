from pathlib import Path

from ideo import common, sfx as sfx_mod

PAUSE = 1.2
MAX_WORDS = 60


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


def compact(words: list[dict], sfx: list[dict], info: dict) -> str:
    body = []
    pending = sorted(sfx, key=lambda m: m["s"])
    current: list[dict] = []

    def flush():
        if current:
            body.append(f"[{common.fmt_ts(current[0]['s'])}] " + " ".join(w["w"] for w in current))
            current.clear()

    def emit_sfx_before(limit: float):
        while pending and pending[0]["s"] < limit:
            flush()
            marker = pending.pop(0)
            body.append(f"[son {common.fmt_ts(marker['s'])} {marker['e'] - marker['s']:.1f}s]")

    previous_end = None
    for word in words:
        emit_sfx_before(word["s"])
        if current and (len(current) >= MAX_WORDS or word["s"] - previous_end >= PAUSE):
            flush()
        current.append(word)
        previous_end = word["e"]
    flush()
    emit_sfx_before(float("inf"))
    return "\n".join(header(info)) + "\n\n" + "\n".join(body) + "\n"


def prepare_transcript(job: Path) -> dict:
    job = Path(job)
    out = job / "transcript_compact.md"
    sfx_path = job / "sfx.json"
    lang = (job / "lang.txt").read_text(encoding="utf-8").strip()
    words = common.load_json(job / "words.json")
    step = common.read_status(job)["steps"].get("transcript")
    if step and step["ok"] and out.exists() and sfx_path.exists():
        markers = common.load_json(sfx_path)
        text = out.read_text(encoding="utf-8")
    else:
        info = {**common.load_json(job / "info.json"), "language": lang}
        rms = sfx_mod.rms_db_per_second(job / "source.wav")
        markers = sfx_mod.find_sfx(rms, words)
        text = compact(words, markers, info)
        common.save_json(sfx_path, markers)
        out.write_text(text, encoding="utf-8")
        common.mark(job, "transcript", True, f"{len(words)} mots, {len(markers)} repères de sons")
    paragraphs = sum(1 for line in text.splitlines() if line.startswith("[") and not line.startswith("[son "))
    return {"words": len(words), "paragraphs": paragraphs, "sfx": len(markers), "lang": lang}
