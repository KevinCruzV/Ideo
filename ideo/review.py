import math
import re
from pathlib import Path

from ideo import plan_check, target, textmatch
from ideo.common import load_json

LIMIT = 8
MAX_PASSES = 2
YEAR = re.compile(r"(?<!\d)(1\d{3}|20\d{2}|2100)(?!\d)")
DRAWING_TYPES = frozenset({"object-state", "versus", "shape-diagram", "timeline", "mascot"})
LIST_FIELDS = {"fact-chips": "chips", "stack-list": "items"}
LONG_SAY = 30
BARE_WORDS = 3
MAX_VERSUS = 3
GROUPED_MIN_WORDS = 18
BREAK_MIN_SCENES = 10
PERCENT = re.compile(r"%|pour cent|percent|prozent|por ciento|per cento|procent|yuzde")
SHORT_SAY = 8
MAX_MASCOTS = 4
KEY_TITLE_SPAN = 6
MAX_SCENES_PER_MINUTE = 9
SURVEY_SHARE = 0.6
GRAVE = {
    "fr": ("mort", "morts", "morte", "mortes", "tue", "tues", "tuee", "tuees", "victime", "victimes", "attentat",
           "attentats", "deces", "massacre", "massacres", "assassine", "assassines"),
    "en": ("death", "deaths", "dead", "killed", "died", "victim", "victims", "massacre", "murdered"),
    "es": ("muerte", "muertes", "muerto", "muertos", "asesinado", "asesinados", "victima", "victimas", "atentado"),
    "de": ("tod", "tote", "toten", "getotet", "opfer", "anschlag", "massaker"),
    "it": ("morte", "morti", "uccisi", "ucciso", "vittima", "vittime", "attentato"),
    "pt": ("morte", "mortes", "mortos", "morto", "vitima", "vitimas", "atentado", "assassinado"),
    "nl": ("dood", "doden", "gedood", "slachtoffer", "slachtoffers", "aanslag"),
    "pl": ("smierc", "zabici", "zabity", "ofiary", "ofiara", "zamach"),
    "tr": ("olum", "olu", "olumler", "kurban", "kurbanlar", "saldiri"),
}
GRAVE_ALL = frozenset(w for words in GRAVE.values() for w in words)


def _scene_where(part: int, index: int) -> str:
    return f"Partie {part}, scène {index}"


def _screen_values(value):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield str(int(value)) if float(value).is_integer() else str(value)
    elif isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _screen_values(v)
    elif isinstance(value, list):
        for v in value:
            yield from _screen_values(v)


def _words(text: str) -> list[str]:
    return [n for part in re.split(r"[\s\-'’]+", text) if (n := textmatch.normalize(part))]


def _list_texts(scene: dict) -> list[str]:
    props = scene.get("props") or {}
    kind = scene.get("type")
    if kind in LIST_FIELDS:
        values = props.get(LIST_FIELDS[kind])
        return [v for v in values if isinstance(v, (str, int, float))] if isinstance(values, list) else []
    if kind == "icon-grid":
        cells = props.get("cells")
        return [c.get("label") for c in cells if isinstance(c, dict) and isinstance(c.get("label"), str)] \
            if isinstance(cells, list) else []
    return []


def _bare_names(scene: dict) -> bool:
    texts = _list_texts(scene)
    if len(texts) < 2:
        return False
    if scene.get("type") == "icon-grid" and not _has_drawing(scene):
        return True
    return all(isinstance(t, str) and len(t.split()) <= BARE_WORDS and not re.search(r"\d", t) for t in texts)


def _has_drawing(scene: dict) -> bool:
    props = scene.get("props") or {}
    if scene.get("type") in DRAWING_TYPES or props.get("picto"):
        return True
    cells = props.get("cells")
    return scene.get("type") == "icon-grid" and isinstance(cells, list) and any(
        isinstance(c, dict) and c.get("picto") for c in cells)


def _grouped_early(scene: dict) -> bool:
    say = _say(scene)
    words = say.split()
    items = scene.get("items")
    if len(words) <= GROUPED_MIN_WORDS or not isinstance(items, list) or not items:
        return False
    positions = []
    for item in items:
        anchor = textmatch.anchor_text(item.get("on")) if isinstance(item, dict) else None
        span = textmatch.find_span(words, anchor) if anchor else None
        if span is None:
            return False
        positions.append(span[0])
    return all(p < len(words) / 2 for p in positions)


def _say(scene: dict) -> str:
    say = scene.get("say")
    return say if isinstance(say, str) else ""


def _has_date(scene: dict) -> bool:
    props = scene.get("props") or {}
    if props.get("kicker"):
        return True
    return any(YEAR.search(text) for text in _screen_values(props))


def _line(code: str, where: str, finding: str, todo: str) -> tuple[str, str]:
    return code, f"RELIRE : {where} : {finding}. {todo}"


def _scene_list(indexes: list[int]) -> str:
    return ", ".join(str(i) for i in indexes)


def _part_findings(part: dict, n: int, out: list) -> None:
    scenes = part["scenes"]
    where = f"Partie {n}"
    count = len(scenes)
    for i, scene in enumerate(scenes, 1):
        say = _say(scene)
        props = scene.get("props") or {}
        kind = scene.get("type")
        if kind == "counter" and set(_words(say)) & GRAVE_ALL:
            out.append((2, *_line("compteur-sujet-grave", _scene_where(n, i), "un compteur accompagne un sujet grave",
                                 "Remplace le compteur par une scène sobre (stamp, key-title ou timeline), sans animation de chiffre")))
        if YEAR.search(say) and not _has_date(scene):
            out.append((2, *_line("annee-sans-kicker", _scene_where(n, i), "le texte cite une année qui n'apparaît pas à l'écran",
                                 "Ajoute un « kicker » avec la date ou mets l'année dans les props")))
        if kind == "counter" and not props.get("unit") and PERCENT.search(say.lower()):
            out.append((2, *_line("compteur-sans-unite", _scene_where(n, i), "compteur sans unité alors que le « say » parle de pourcentage",
                                  "Ajoute « unit » (par exemple « % ») sur le compteur")))
        if _grouped_early(scene):
            out.append((2, *_line("items-groupes-debut", _scene_where(n, i),
                                  "éléments groupés au début : tous les « items » sont ancrés dans la première moitié du « say », la fin de la scène reste figée",
                                  "Ancre le dernier élément sur un mot de la dernière phrase")))
        if kind == "shape-diagram" and props.get("shape") == "bar" and not props.get("unit"):
            out.append((2, *_line("barres-sans-unite", _scene_where(n, i), "un diagramme en barres sans unité",
                                 "Ajoute « unit » (par exemple « Md$ » ou « % ») pour que les valeurs aient un sens")))
        if kind in ("fact-chips", "stack-list", "icon-grid") and _bare_names(scene):
            out.append((3, *_line("liste-nue", _scene_where(n, i), "une liste de noms nus, sans chiffre ni explication",
                                 "Ajoute un chiffre ou un détail à chaque entrée, ou remplace la scène par un dessin")))
    drawn = sum(1 for s in scenes if _has_drawing(s))
    if count and drawn * 2 < count:
        bare = sorted((i for i, s in enumerate(scenes, 1) if not _has_drawing(s)),
                      key=lambda i: -len(_say(scenes[i - 1]).split()))[:3]
        out.append((2, *_line("peu-de-dessins", where, f"seulement {drawn} scène(s) sur {count} montrent un dessin",
                             f"Ajoute un « picto » ou un dessin aux scènes sans dessin les plus longues : {_scene_list(sorted(bare))}")))
    for a, b in zip(range(1, count), range(2, count + 1)):
        if scenes[a - 1].get("type") == scenes[b - 1].get("type"):
            out.append((3, *_line("meme-type-suite", f"{where}, scènes {a} et {b}", f"deux scènes de suite du même type « {scenes[a - 1].get('type')} »",
                                 "Change le type d'une des deux pour varier le visuel")))
            break
    if count > BREAK_MIN_SCENES and not any(s.get("break") is True for s in scenes):
        out.append((3, *_line("sans-pause-d-acte", where, f"{count} scènes sans aucune pause d'acte",
                              "Ajoute « \"break\": true » sur la première scène de chaque nouvel acte pour marquer une pause")))
    versus = sum(1 for s in scenes if s.get("type") == "versus")
    if versus > MAX_VERSUS:
        out.append((3, *_line("trop-de-versus", where, f"{versus} scènes « versus »", f"Garde-en {MAX_VERSUS} au plus, remplace les autres")))
    mascots = sum(1 for s in scenes if s.get("type") == "mascot")
    if mascots > MAX_MASCOTS:
        out.append((3, *_line("trop-de-mascot", where, f"{mascots} scènes « mascot »", f"Garde-en {MAX_MASCOTS} au plus, remplace les autres")))
    titles = sum(1 for s in scenes if s.get("type") == "key-title")
    if titles > math.ceil(count / KEY_TITLE_SPAN):
        out.append((3, *_line("trop-de-key-title", where, f"{titles} scènes « key-title » pour {count} scènes",
                             f"Garde au plus un « key-title » toutes les {KEY_TITLE_SPAN} scènes")))
    long = [i for i, s in enumerate(scenes, 1) if len(_say(s).split()) > LONG_SAY]
    if long:
        out.append((3, *_line("say-trop-long", where, f"scène(s) {_scene_list(long)} de plus de {LONG_SAY} mots de « say »",
                             "Coupe en deux scènes ou raccourcis le texte")))
    short = [i for i, s in enumerate(scenes, 1) if len(_say(s).split()) < SHORT_SAY]
    if short:
        out.append((3, *_line("say-trop-court", where, f"scène(s) {_scene_list(short)} de moins de {SHORT_SAY} mots de « say »",
                             "Fusionne avec une scène voisine ou développe le texte")))
    if scenes and _say(scenes[-1]).strip().endswith("?"):
        out.append((1, *_line("fin-en-question", _scene_where(n, count), "la dernière scène est une question",
                             "Finis par la réponse à l'accroche, pas par une question")))
    for i in range(count - 2):
        firsts = [(_words(_say(scenes[i + k])) or [""])[0] for k in range(3)]
        if firsts[0] and firsts[0] == firsts[1] == firsts[2]:
            out.append((3, *_line("debuts-identiques", f"{where}, scènes {i + 1} à {i + 3}", f"trois « say » de suite commencent par « {firsts[0]} »",
                                 "Varie les débuts de phrase")))
            break


def _coverage(plan: dict, duration: float | None) -> float:
    marks = []
    for part in plan["parts"]:
        for scene in part["scenes"]:
            try:
                marks.append(plan_check.parse_ts(scene["src"]))
            except (KeyError, TypeError, ValueError):
                continue
    if not marks or not duration:
        return 0.0
    return (max(marks) - min(marks)) / duration


def coded(plan: dict, job: Path, seconds: int) -> list[tuple[str, str]]:
    scored: list[tuple[int, str, str]] = []
    for part in plan["parts"]:
        _part_findings(part, part["n"], scored)
    total = sum(len(p["scenes"]) for p in plan["parts"])
    if seconds and total / (seconds / 60) > MAX_SCENES_PER_MINUTE:
        scored.append((1, *_line("rythme-hache", "Plan", f"{total} scènes pour environ {seconds} s, plus de {MAX_SCENES_PER_MINUTE} scènes par minute (rythme haché)",
                                "Fusionne des scènes ou allonge les « say »")))
    info = plan_check.read_json(job, "info.json", {})
    duration = info.get("duration") if isinstance(info, dict) else None
    if isinstance(duration, (int, float)) and not isinstance(duration, bool) and duration > 0:
        _, ranges = plan_check.sponsor_ranges(job, info)
        low, _ = target.bounds(target.useful_seconds(float(duration), ranges))
        if seconds < low and _coverage(plan, float(duration)) > SURVEY_SHARE:
            scored.append((1, *_line("survol", "Plan", f"durée estimée {seconds} s, sous les {low} s conseillés, alors que les « src » couvrent plus de {round(SURVEY_SHARE * 100)} % de la source",
                                    "Tu survoles toute la source en peu de temps : garde moins d'événements ou explique davantage chacun")))
    kickers = any(isinstance(s.get("props"), dict) and s["props"].get("kicker")
                  for p in plan["parts"] for s in p["scenes"])
    if not kickers:
        scored.append((3, *_line("sans-kicker", "Plan", "aucun « kicker » dans tout le plan",
                                "Ajoute un « kicker » (date, lieu, acte) sur les scènes qui changent de moment ou de lieu")))
    return [(code, text) for _, code, text in sorted(scored, key=lambda item: item[0])]


def findings(plan: dict, job: Path, seconds: int) -> list[str]:
    return [text for _, text in coded(plan, job, seconds)]


def passes(job: Path) -> int:
    data = plan_check.read_json(job, "review.json", {})
    count = data.get("count") if isinstance(data, dict) else 0
    return count if isinstance(count, int) and count >= 0 else 0


def record_pass(job: Path) -> None:
    from ideo.common import save_json

    save_json(Path(job) / "review.json", {"count": passes(job) + 1})


def reset(job: Path) -> None:
    (Path(job) / "review.json").unlink(missing_ok=True)


def relire_coded(job: Path, plan: dict, seconds: int) -> list[tuple[str, str]]:
    if passes(job) >= MAX_PASSES:
        return []
    pairs = coded(plan, job, seconds)[:LIMIT]
    if pairs:
        record_pass(job)
    return pairs


def relire(job: Path, plan: dict, seconds: int) -> list[str]:
    return [text for _, text in relire_coded(job, plan, seconds)]
