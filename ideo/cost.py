from pathlib import Path

from ideo import common, plan_check, target

REPO = Path(__file__).resolve().parent.parent
SKILL_FILES = (REPO / "skills" / "ideo" / "SKILL.md", REPO / "skills" / "ideo" / "references" / "plan-guide.md",
               REPO / "skills" / "ideo" / "references" / "lecons.md")
SKILL_LANG = "fr"
CHARS_PER_TOKEN = {"fr": 3.3, "en": 4.0}
OTHER_CHARS_PER_TOKEN = 3.5
OUTPUT_SHARE = 0.15
LONG_CONTENT_FACTOR = 2.0
READ_TOKENS = 15000
READ_MAX_LINES = 2000
WRITE_TOKENS_PER_SECOND = 17
WRITE_SPREAD = 1.6


def ratio(lang: str) -> float:
    return CHARS_PER_TOKEN.get(lang, OTHER_CHARS_PER_TOKEN)


def tokens(chars: int, lang: str) -> int:
    return round(chars / ratio(lang))


def round_hundred(value: float) -> int:
    return int(round(value / 100.0)) * 100


def fmt(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _chars(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8"))
    except OSError:
        return 0


def _lang(job: Path) -> str:
    try:
        return (job / "lang.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def speech_words(job: Path) -> int:
    info = plan_check.read_json(job, "info.json", {})
    words = plan_check.read_json(job, "words.json", [])
    _, ranges = plan_check.sponsor_ranges(job, info if isinstance(info, dict) else {})
    count = 0
    for w in words if isinstance(words, list) else []:
        try:
            mid = (float(w["s"]) + float(w["e"])) / 2
        except (KeyError, TypeError, ValueError):
            continue
        if not any(s <= mid < e for s, e in ranges):
            count += 1
    return count


def _source(duration) -> str:
    if not isinstance(duration, (int, float)):
        return "0 min"
    if duration < 60:
        return f"{round(duration)} s"
    return f"{round(duration / 60)} min"


def estimate(job: Path) -> dict:
    job = Path(job)
    lang = _lang(job)
    transcript = round_hundred(tokens(_chars(job / "transcript_compact.md"), lang))
    skill = round_hundred(tokens(sum(_chars(p) for p in SKILL_FILES), SKILL_LANG))
    spoken = speech_words(job) / plan_check.RATES.get(lang, 2.6)
    content = max(plan_check.MIN_SECONDS, spoken * OUTPUT_SHARE)
    seconds = min(content, plan_check.MAX_SECONDS)
    info = plan_check.read_json(job, "info.json", {})
    duration = info.get("duration") if isinstance(info, dict) else None
    return {
        "transcript": transcript,
        "skill": skill,
        "reading": transcript + skill,
        "seconds": seconds,
        "long": content > plan_check.MAX_SECONDS * LONG_CONTENT_FACTOR,
        "write_low": round_hundred(seconds * WRITE_TOKENS_PER_SECOND),
        "write_high": round_hundred(seconds * WRITE_TOKENS_PER_SECOND * WRITE_SPREAD),
        "minutes": round(duration / 60) if isinstance(duration, (int, float)) else 0,
        "source": _source(duration),
    }


def line(job: Path) -> str:
    e = estimate(job)
    text = (f"lecture au moins ~{fmt(e['reading'])} tokens (transcription {fmt(e['transcript'])} + skill et guide {fmt(e['skill'])}), "
            f"écriture ~{fmt(e['write_low'])} à {fmt(e['write_high'])} tokens, source {e['source']}")
    if e["long"]:
        text += ", contenu long : une vidéo de 5 min ou plusieurs parties"
    return text


def advice(job: Path) -> str:
    text = target.for_job(job)
    return f" {text}" if text else ""


def reading(job: Path) -> dict:
    job = Path(job)
    try:
        lines = (job / "transcript_compact.md").read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    budget = int(READ_TOKENS * ratio(_lang(job)))
    if sum(len(x) + 1 for x in lines) <= budget and len(lines) <= READ_MAX_LINES:
        return {"lines": len(lines), "chunk": None, "offsets": []}
    longest = max(len(x) + 1 for x in lines)
    chunk = max(1, min(READ_MAX_LINES, budget // longest))
    return {"lines": len(lines), "chunk": chunk, "offsets": list(range(1, len(lines) + 1, chunk))}


def reading_note(job: Path) -> str:
    plan = reading(job)
    if plan["chunk"] is None:
        return f"{plan['lines']} lignes, à lire en un seul Read"
    offsets = ", ".join(str(o) for o in plan["offsets"])
    return (f"{plan['lines']} lignes, trop longue pour un seul Read : lis-la en {len(plan['offsets'])} Read consécutifs, "
            f"offset {offsets}, chacun avec limit {plan['chunk']}")
