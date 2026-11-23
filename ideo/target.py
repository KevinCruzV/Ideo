from pathlib import Path

from ideo import plan_check, speed

TABLE = ((240, (65, 100)), (600, (90, 150)), (float("inf"), (120, 180)))
HARD_MAX = 300


def merged(ranges: list) -> list[tuple[float, float]]:
    out: list[list[float]] = []
    for s, e in sorted((float(s), float(e)) for s, e in ranges if e > s):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [(s, e) for s, e in out]


def useful_seconds(duration: float, ranges: list) -> float:
    cut = sum(min(e, duration) - max(s, 0.0) for s, e in merged(ranges) if min(e, duration) > max(s, 0.0))
    return max(duration - cut, 0.0)


def bounds(useful: float) -> tuple[int, int]:
    return next(b for limit, b in TABLE if useful < limit)


def words(low: int, high: int, lang: str) -> tuple[int, int]:
    rate = speed.rate(lang)
    return round(low * rate), round(high * rate)


def line(duration: float, ranges: list, lang: str) -> str:
    low, high = bounds(useful_seconds(duration, ranges))
    a, b = words(low, high, lang)
    return (f"Durée conseillée : {low} à {high} s (environ {a} à {b} mots de say). "
            f"Plus court si l'histoire tient, jusqu'à {HARD_MAX} s si elle en a besoin.")


def for_job(job: Path) -> str | None:
    job = Path(job)
    info = plan_check.read_json(job, "info.json", {})
    duration = info.get("duration") if isinstance(info, dict) else None
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
        return None
    _, ranges = plan_check.sponsor_ranges(job, info)
    try:
        lang = (job / "lang.txt").read_text(encoding="utf-8").strip()
    except OSError:
        lang = "fr"
    return line(float(duration), ranges, lang)
