import math
from pathlib import Path

from ideo import common, plan_check

REPO = Path(__file__).resolve().parent.parent
SKILL_FILES = (REPO / "skills" / "ideo" / "SKILL.md", REPO / "skills" / "ideo" / "references" / "plan-guide.md")
SKILL_LANG = "fr"
CHARS_PER_TOKEN = {"fr": 3.3, "en": 4.0}
OTHER_CHARS_PER_TOKEN = 3.5
OUTPUT_SHARE = 0.15
WRITE_TOKENS_PER_SECOND = 17
WRITE_SPREAD = 1.6


def tokens(chars: int, lang: str) -> int:
    return round(chars / CHARS_PER_TOKEN.get(lang, OTHER_CHARS_PER_TOKEN))


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


def estimate(job: Path) -> dict:
    job = Path(job)
    lang = _lang(job)
    transcript = round_hundred(tokens(_chars(job / "transcript_compact.md"), lang))
    skill = round_hundred(tokens(sum(_chars(p) for p in SKILL_FILES), SKILL_LANG))
    spoken = speech_words(job) / plan_check.RATES.get(lang, 2.6)
    seconds = max(plan_check.MIN_SECONDS, spoken * OUTPUT_SHARE)
    videos = min(plan_check.MAX_PARTS, max(1, math.ceil(seconds / plan_check.MAX_SECONDS)))
    seconds = min(seconds, plan_check.MAX_SECONDS * videos)
    info = plan_check.read_json(job, "info.json", {})
    duration = info.get("duration") if isinstance(info, dict) else None
    return {
        "transcript": transcript,
        "skill": skill,
        "reading": transcript + skill,
        "seconds": seconds,
        "videos": videos,
        "write_low": round_hundred(seconds * WRITE_TOKENS_PER_SECOND),
        "write_high": round_hundred(seconds * WRITE_TOKENS_PER_SECOND * WRITE_SPREAD),
        "minutes": round(duration / 60) if isinstance(duration, (int, float)) else 0,
    }


def line(job: Path) -> str:
    e = estimate(job)
    videos = "1 vidéo attendue" if e["videos"] == 1 else f"{e['videos']} vidéos attendues"
    return (f"lecture ~{fmt(e['reading'])} tokens (transcription {fmt(e['transcript'])} + skill et guide {fmt(e['skill'])}), "
            f"écriture ~{fmt(e['write_low'])} à {fmt(e['write_high'])} tokens, source {e['minutes']} min, {videos}")
