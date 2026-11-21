import json
from datetime import date
from pathlib import Path

from ideo import common

RECENT = 5


def path() -> Path:
    return common._root() / "historique.json"


def _empty() -> dict:
    return {"jobs": {}, "order": [], "videos_since": 0, "entretien": None}


def load() -> dict:
    try:
        data = json.loads(path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _empty()
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), dict):
        return _empty()
    base = _empty()
    base["jobs"] = {k: v for k, v in data["jobs"].items() if isinstance(v, dict)}
    order = data.get("order")
    base["order"] = [o for o in order if o in base["jobs"]] if isinstance(order, list) else list(base["jobs"])
    since = data.get("videos_since")
    base["videos_since"] = since if isinstance(since, int) and since >= 0 else 0
    entretien = data.get("entretien")
    base["entretien"] = entretien if isinstance(entretien, dict) else None
    return base


def _save(data: dict) -> None:
    try:
        path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def _entry(data: dict, job) -> dict:
    name = Path(str(job)).name
    entry = data["jobs"].setdefault(name, {"id": name, "date": date.today().isoformat()})
    if name in data["order"]:
        data["order"].remove(name)
    data["order"].append(name)
    return entry


def note_plan(job, lang: str | None = None, source=None, scenes: int | None = None) -> None:
    data = load()
    entry = _entry(data, job)
    if lang:
        entry["lang"] = lang
    if isinstance(source, (int, float)) and not isinstance(source, bool):
        entry["source"] = source
    if scenes is not None:
        entry["scenes"] = scenes
    _save(data)


def add_errors(job, counts: dict) -> None:
    data = load()
    entry = _entry(data, job)
    errors = entry.get("errors") if isinstance(entry.get("errors"), dict) else {}
    for code, n in counts.items():
        errors[code] = errors.get(code, 0) + n
    entry["errors"] = errors
    _save(data)


def add_relire(job, codes: list) -> None:
    data = load()
    entry = _entry(data, job)
    if "relire" not in entry:
        entry["relire"] = list(codes)
    _save(data)


def add_qc(job, codes: list) -> None:
    data = load()
    entry = _entry(data, job)
    entry["qc"] = sorted(set(codes))
    _save(data)


def record_produce(job, seconds: float | None) -> None:
    data = load()
    entry = _entry(data, job)
    if seconds is not None:
        entry["produced"] = round(seconds, 1)
    data["videos_since"] += 1
    _save(data)


def videos_since() -> int:
    return load()["videos_since"]


def job_codes(entry: dict) -> set:
    codes = set()
    errors = entry.get("errors")
    if isinstance(errors, dict):
        codes |= set(errors)
    for key in ("relire", "qc"):
        value = entry.get(key)
        if isinstance(value, list):
            codes |= {c for c in value if isinstance(c, str)}
    return codes


def recent_codes(limit: int = RECENT) -> dict:
    data = load()
    counts: dict = {}
    for name in data["order"][-limit:]:
        for code in job_codes(data["jobs"][name]):
            counts[code] = counts.get(code, 0) + 1
    return counts


def all_codes() -> dict:
    counts: dict = {}
    for entry in load()["jobs"].values():
        for code in job_codes(entry):
            counts[code] = counts.get(code, 0) + 1
    return counts


def _entretien(status: str, detail: str) -> None:
    data = load()
    data["videos_since"] = 0
    data["entretien"] = {"status": status, "date": date.today().isoformat(), "detail": " ".join(detail.split()),
                         "shown": False}
    _save(data)


def entretien_done(summary: str) -> None:
    _entretien("fait", summary)


def entretien_failed(reason: str) -> None:
    _entretien("echec", reason)


def last_entretien() -> dict | None:
    return load()["entretien"]


def take_notice() -> str | None:
    data = load()
    entretien = data["entretien"]
    if not entretien or entretien.get("shown"):
        return None
    entretien["shown"] = True
    _save(data)
    detail = entretien.get("detail") or ""
    if entretien.get("status") == "echec":
        return f"Dernier entretien : échec, {detail or 'raison inconnue'}."
    return f"Dernier entretien : {entretien.get('date')}" + (f", {detail}." if detail else ".")
