import re
from pathlib import Path

from ideo import codes, common, config, history, learn, retours

BACKLOG = 8
SIMILAR = 0.6
TOP_CODES = 10
TAG = re.compile(r"\(auto:[\w-]+\) ")


def path() -> Path:
    return common._root() / "entretien.md"


def reasons() -> list[str]:
    out = []
    since = history.videos_since()
    if since >= config.entretien_seuil():
        out.append(f"{since} vidéos depuis le dernier entretien")
    open_entries = retours.count_unchecked()
    if open_entries >= BACKLOG:
        out.append(f"{open_entries} retours non traités")
    return out


def notice() -> str | None:
    why = reasons()
    if not why:
        return None
    head = "Entretien à lancer" if config.entretien_auto() else "Entretien conseillé"
    return f"{head} : {' et '.join(why)}."


def _words(text: str) -> set:
    return {w for w in re.sub(r"[\W_]+", " ", TAG.sub("", text).lower()).split() if len(w) > 3}


def duplicates(lessons: list[str]) -> list[tuple[str, str]]:
    sets = [_words(text) for text in lessons]
    out = []
    for i in range(len(lessons)):
        for j in range(i + 1, len(lessons)):
            union = sets[i] | sets[j]
            if union and len(sets[i] & sets[j]) / len(union) >= SIMILAR:
                out.append((lessons[i], lessons[j]))
    return out


def _summary_counts() -> tuple[int, int, int, int]:
    defects = len(retours.unchecked(retours.SIGNALES)) + len(retours.unchecked(retours.DETECTES))
    wishes = len(retours.wishes())
    lessons = len(learn.existing(learn.lessons_path()))
    return history.videos_since(), defects, wishes, lessons


def write() -> tuple[Path, tuple[int, int, int, int]]:
    since, defects, wishes, lessons = counts = _summary_counts()
    last = history.last_entretien()
    if last:
        detail = last.get("detail") or ""
        done = f"{last.get('date')}, " + ("échec, " if last.get("status") == "echec" else "") + detail
    else:
        done = "jamais"
    lines = ["# Entretien d'ideo", "", f"- Vidéos depuis le dernier entretien : {since}",
             f"- Dernier entretien : {done.rstrip(', ')}", "", "## Codes les plus fréquents", ""]
    frequent = sorted(history.all_codes().items(), key=lambda pair: (-pair[1], pair[0]))[:TOP_CODES]
    lines += [f"- {code} : {n} job(s)" + ("" if code in codes.LESSONS or code in codes.CODE_ONLY else " (sans leçon)")
              for code, n in frequent] or ["- aucun"]
    lines += ["", f"## Défauts à traiter ({defects})", ""]
    entries = [f"[signalé] {e}" for e in retours.unchecked(retours.SIGNALES)]
    entries += [f"[détecté] {e}" for e in retours.unchecked(retours.DETECTES)]
    lines += [f"- {e}" for e in entries] or ["- aucun"]
    lines += ["", f"## Dessins manquants ({wishes})", ""]
    lines += [f"- {text} (×{n})" if n > 1 else f"- {text}" for text, n in retours.wishes()] or ["- aucun"]
    known = learn.existing(learn.lessons_path())
    lines += ["", f"## Leçons ({lessons})", ""] + ([f"- {k}" for k in known] or ["- aucune"])
    similar = duplicates(known)
    lines += ["", "## Doublons probables", ""]
    lines += [f"- {a} | {b}" for a, b in similar] or ["- aucun"]
    path().write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path(), counts


def report_line() -> str:
    file, (since, defects, wishes, lessons) = write()
    return (f"OK entretien : {file} ({since} vidéos depuis le dernier entretien, {defects} défauts, "
            f"{wishes} dessins manquants, {lessons} leçons)")
