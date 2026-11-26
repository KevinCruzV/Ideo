import json
import math
import re
from pathlib import Path

from ideo import countries, plan_check, scene_schema, slop, target, textmatch
from ideo.common import load_json

LIMIT = 8
MAX_PASSES = 3
YEAR = re.compile(r"(?<!\d)(1\d{3}|20\d{2}|2100)(?!\d)")
DRAWING_TYPES = frozenset({"object-state", "versus", "shape-diagram", "timeline", "mascot", "artwork"})
LIST_FIELDS = {"fact-chips": "chips", "stack-list": "items"}
LONG_SAY = 20
BARE_WORDS = 3
MAX_VERSUS = 2
PERSON_NAME_WORDS = 5
COUNTER_EARLY_SHARE = 3
MAX_SAME_PICTO = 2
APPEARANCE = ("hair", "hair_color", "facial", "hat", "glasses", "outfit", "skin", "gender", "age", "job")
MIN_CITED = 3
ROUTE_WORDS = frozenset({"route", "routes", "trajet", "trajets", "chemin", "chemins", "traverse", "traversent", "traversant",
                         "frontiere", "frontieres", "canal", "canaux"})
BODY_MIN_SCENES = 5
BODY_MAX_MARKS = 4
BODY_PARTS_WORDS = {
    "dos": "back", "back": "back", "ventre": "stomach", "belly": "stomach", "estomac": "stomach", "stomach": "stomach",
    "cou": "neck", "nuque": "neck", "neck": "neck", "coeur": "heart", "heart": "heart", "poumon": "lungs",
    "poumons": "lungs", "lungs": "lungs", "colonne": "spine", "spine": "spine", "hanche": "hips", "hanches": "hips",
    "hips": "hips", "genou": "knees", "genoux": "knees", "knees": "knees", "tete": "head", "head": "head",
    "gorge": "throat", "throat": "throat", "cerveau": "brain", "brain": "brain", "epaule": "shoulders",
    "epaules": "shoulders", "shoulders": "shoulders", "bras": "arms", "arms": "arms", "main": "hands", "mains": "hands",
    "hands": "hands", "jambe": "legs", "jambes": "legs", "legs": "legs", "pied": "feet", "pieds": "feet", "feet": "feet",
    "poitrine": "chest", "chest": "chest",
}
_ARTICLES_EN = frozenset({"the", "a", "an", "your", "my", "his", "her", "their", "our", "its", "lower", "upper", "bad", "sore", "stiff"})
_ARTICLES_FR = frozenset({"la", "une", "ma", "ta", "sa", "notre", "votre", "leur", "cette"})
AMBIGUOUS_PARTS = {"back": _ARTICLES_EN, "head": _ARTICLES_EN, "feet": _ARTICLES_EN, "main": _ARTICLES_FR}
POSTURE_WORDS = {
    "allonge": "lying-back", "allongee": "lying-back", "allonges": "lying-back", "allongees": "lying-back",
    "couche": "lying-back", "couchee": "lying-back", "couches": "lying-back", "lying": "lying-back", "laid": "lying-back",
    "assis": "sitting", "assise": "sitting", "assises": "sitting", "sitting": "sitting", "seated": "sitting",
    "debout": "standing", "standing": "standing",
}
POSTURE_PHRASES = {("sur", "le", "cote"): "lying-side-left", ("on", "your", "side"): "lying-side-left",
                   ("sur", "le", "ventre"): "lying-stomach", ("on", "your", "stomach"): "lying-stomach"}
CROWDED = {"timeline": ("marks", 5, ("marks.at", "marks.label")), "stack-list": ("items", 5, ("items",)),
           "icon-grid": ("cells", 7, ("cells.label",)), "shape-diagram": ("values", 6, ("labels",))}
CROWDED_RATIO = 0.5
GROUPED_MIN_WORDS = 18
BREAK_MIN_SCENES = 10
PERCENT = re.compile(r"%|pour cent|percent|prozent|por ciento|per cento|procent|yuzde")
SHORT_SAY = 8
MAX_MASCOTS = 4
KEY_TITLE_SPAN = 6
MAX_SCENES_PER_MINUTE = 20
SURVEY_SHARE = 0.6
SURVEY_MINIMUM_SHARE = 0.6
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


def _texts_of(props: dict, path: str) -> list[str]:
    return [str(v) for _, v in scene_schema._capped(props, path) if isinstance(v, (str, int, float)) and not isinstance(v, bool)]


def _crowded(scene: dict) -> bool:
    rule = CROWDED.get(scene.get("type"))
    props = scene.get("props")
    if not rule or not isinstance(props, dict):
        return False
    field, minimum, paths = rule
    values = props.get(field)
    if not isinstance(values, list) or len(values) < minimum:
        return False
    caps = scene_schema.TEXT_CAPS[scene["type"]]
    ratios = [scene_schema.screen_length(t.strip()) / caps[path] for path in paths for t in _texts_of(props, path)]
    return bool(ratios) and sum(ratios) / len(ratios) > CROWDED_RATIO


def _flag_codes(props: dict) -> set:
    values = [props.get(k) for k in ("picto", "left_picto", "right_picto")]
    cells = props.get("cells")
    values += [c.get("picto") for c in cells if isinstance(c, dict)] if isinstance(cells, list) else []
    return {v[len("flag:"):] for v in values if isinstance(v, str) and v.startswith("flag:")}


def _country_labels(scene: dict) -> list[str]:
    props = scene.get("props") or {}
    kind = scene.get("type")
    if kind == "versus":
        return [props.get(k) for k in ("left", "right")]
    return _list_texts(scene) if kind in ("icon-grid", "fact-chips", "stack-list") else []


def _missing_flags(scene: dict) -> list[tuple[str, str]]:
    props = scene.get("props") or {}
    have = _flag_codes(props) if isinstance(props, dict) else set()
    missing = []
    for label in _country_labels(scene):
        code = countries.code_of(label)
        if code and code not in have and (label, code) not in missing:
            missing.append((label, code))
    return missing


def _tokens_of(say: str) -> list[str]:
    return countries.plain(say).split()


def _body_hits(say: str) -> tuple[list[str], list[str]]:
    tokens = _tokens_of(say)
    parts = [BODY_PARTS_WORDS[t] for i, t in enumerate(tokens)
             if t in BODY_PARTS_WORDS and (t not in AMBIGUOUS_PARTS or (i > 0 and tokens[i - 1] in AMBIGUOUS_PARTS[t]))]
    postures = [POSTURE_WORDS[t] for t in tokens if t in POSTURE_WORDS]
    postures += [pose for phrase, pose in POSTURE_PHRASES.items()
                 if any(tuple(tokens[i:i + len(phrase)]) == phrase for i in range(len(tokens)))]
    return parts, postures


def _pose_for(scenes: list) -> str:
    for scene in scenes:
        tokens = _tokens_of(_say(scene))
        for phrase, pose in POSTURE_PHRASES.items():
            if any(tuple(tokens[i:i + len(phrase)]) == phrase for i in range(len(tokens))):
                return pose
        for token in tokens:
            if token in POSTURE_WORDS:
                return POSTURE_WORDS[token]
    return "standing"


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


def _anchor_index(scene: dict, el: str) -> int | None:
    items = scene.get("items")
    if not isinstance(items, list):
        return None
    words = _say(scene).split()
    for item in items:
        if isinstance(item, dict) and item.get("el") == el:
            anchor = textmatch.anchor_text(item.get("on"))
            span = textmatch.find_span(words, anchor) if anchor else None
            return span[0] if span else None
    return None


def _has_date(scene: dict) -> bool:
    props = scene.get("props") or {}
    if props.get("kicker"):
        return True
    return any(YEAR.search(text) for text in _screen_values(props))


def _line(code: str, where: str, finding: str, todo: str) -> tuple[str, str]:
    return code, f"RELIRE : {where} : {finding}. {todo}"


def _scene_list(indexes: list[int]) -> str:
    return ", ".join(str(i) for i in indexes)


def _look(props: dict) -> tuple:
    return tuple((k, str(props[k]).strip().lower()) for k in APPEARANCE if props.get(k) not in (None, "", False))


def _unseen_cards(scenes: list) -> list[tuple[int, dict]]:
    return [(i, s.get("props") or {}) for i, s in enumerate(scenes, 1)
            if s.get("type") == "person-card" and isinstance(s.get("props"), dict) and s["props"].get("photo") is not True]


def _same_look(cards: list[tuple[int, dict]]) -> tuple[int, int] | None:
    seen: dict = {}
    for i, props in cards:
        look = _look(props)
        if not look:
            continue
        name = str(props.get("name", "")).strip().lower()
        for other, other_name in seen.get(look, []):
            if other_name != name:
                return other, i
        seen.setdefault(look, []).append((i, name))
    return None


def _pictos_of(scene: dict) -> list[str]:
    props = scene.get("props") or {}
    if not isinstance(props, dict):
        return []
    found = [props.get(k) for k in ("picto", "left_picto", "right_picto")]
    cells = props.get("cells")
    found += [c.get("picto") for c in cells if isinstance(c, dict)] if isinstance(cells, list) else []
    return [v for v in found if isinstance(v, str) and v and not v.startswith(scene_schema.FLAG_PREFIX)]


def _part_findings(part: dict, n: int, out: list, lang: str = "fr") -> None:
    for code, where, finding, todo in slop.findings(part, n, lang):
        out.append((3, *_line(code, where, finding, todo)))
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
        missing = _missing_flags(scene)
        if missing:
            names = ", ".join(f"« {label} » (flag:{code})" for label, code in missing)
            where_to = {"versus": "dans « left_picto » ou « right_picto »", "icon-grid": "dans le « picto » de la cellule"}.get(
                kind, "dans le « picto » de la scène")
            out.append((2, *_line("pays-sans-drapeau", _scene_where(n, i), f"nom de pays sans son drapeau : {names}",
                                  f"Ajoute le drapeau {where_to}")))
        cited = countries.mentions(say) if not _flag_codes(props) else []
        if len(cited) >= MIN_CITED:
            names = ", ".join(name for _, name in cited)
            cells = ", ".join(json.dumps({"picto": f"flag:{code}", "label": name}, ensure_ascii=False) for code, name in cited[:9])
            out.append((2, *_line("pays-cites-sans-drapeaux", _scene_where(n, i),
                                  f"le texte cite {len(cited)} pays ({names}) sans montrer leurs drapeaux",
                                  f"Fais une « icon-grid » avec une cellule par pays : {cells}")))
        if _crowded(scene):
            out.append((2, *_line("scene-trop-chargee", _scene_where(n, i),
                                  f"scène « {kind} » chargée de textes longs",
                                  "Coupe en deux scènes : le rendu devrait sinon réduire le texte sous la taille lisible sur téléphone")))
        if _grouped_early(scene):
            out.append((2, *_line("items-groupes-debut", _scene_where(n, i),
                                  "éléments groupés au début : tous les « items » sont ancrés dans la première moitié du « say », la fin de la scène reste figée",
                                  "Ancre le dernier élément sur un mot de la dernière phrase")))
        if kind == "person-card":
            for el in ("avatar", "name"):
                at = _anchor_index(scene, el)
                if at is not None and at >= PERSON_NAME_WORDS:
                    out.append((2, *_line("carte-nom-tardif", _scene_where(n, i),
                                          f"« {el} » n'apparaît qu'au mot {at + 1} du « say » : la carte reste incomplète pendant que le nom se fait attendre",
                                          "Commence le « say » par le nom de la personne et ancre l'avatar sur ses premiers mots")))
                    break
        if kind == "counter":
            at = _anchor_index(scene, "to")
            total = len(say.split())
            if at is not None and at * COUNTER_EARLY_SHARE >= total:
                out.append((2, *_line("compteur-tardif", _scene_where(n, i),
                                      f"le chiffre du compteur n'apparaît qu'au mot {at + 1} sur {total}, le cadre reste vide jusque-là",
                                      "Ancre « to » sur un des premiers mots du « say »")))
        if kind == "shape-diagram" and props.get("shape") == "bar" and not props.get("unit"):
            out.append((2, *_line("barres-sans-unite", _scene_where(n, i), "un diagramme en barres sans unité",
                                 "Ajoute « unit » (par exemple « Md$ » ou « % ») pour que les valeurs aient un sens")))
        if kind in ("fact-chips", "stack-list", "icon-grid") and _bare_names(scene):
            out.append((3, *_line("liste-nue", _scene_where(n, i), "une liste de noms nus, sans chiffre ni explication",
                                 "Ajoute un chiffre ou un détail à chaque entrée, ou remplace la scène par un dessin")))
    cards = _unseen_cards(scenes)
    bare = [i for i, props in cards if not _look(props)]
    if bare:
        out.append((2, *_line("personnage-sans-apparence", f"{where}, scène{'s' if len(bare) > 1 else ''} {_scene_list(bare)}",
                              "« person-card » sans aucune prop d'apparence",
                              "Ajoute gender, age, job ou hair, outfit, hat pour que le personnage ressemble à la personne")))
    twins = _same_look(cards)
    if twins:
        out.append((2, *_line("personnages-identiques", f"{where}, scènes {twins[0]} et {twins[1]}",
                              "deux personnes différentes ont exactement la même apparence",
                              "Change gender, age, job, hair, hat ou outfit de l'une des deux")))
    counts: dict = {}
    for scene in scenes:
        for name in _pictos_of(scene):
            counts[name.strip().lower()] = counts.get(name.strip().lower(), 0) + 1
    repeated = sorted(n for n, c in counts.items() if c > MAX_SAME_PICTO)
    if repeated:
        listing = ", ".join(f"« {n} » ({counts[n]} fois)" for n in repeated[:3])
        out.append((3, *_line("picto-repete", where, f"un même picto revient plus de {MAX_SAME_PICTO} fois : {listing}",
                              "Remplace les répétitions par d'autres pictos de la liste ou retire-les")))
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
    routes = [(i, countries.mentions(_say(s))) for i, s in enumerate(scenes, 1)
              if set(_tokens_of(_say(s))) & ROUTE_WORDS and len(countries.mentions(_say(s))) >= 2]
    if routes and not any(s.get("type") == "map" for s in scenes):
        first = routes[0][1]
        listing = ", ".join(str(i) for i, _ in routes)
        names = ", ".join(name for _, name in first)
        places = ", ".join(json.dumps({"code": code}) for code, _ in first[:6])
        route = json.dumps([code for code, _ in first[:6]])
        out.append((2, *_line("route-sans-carte", f"{where}, scène{'s' if len(routes) > 1 else ''} {listing}",
                              f"le texte parle d'une route ou d'un trajet entre pays ({names}) sans scène « map »",
                              f"Ajoute une scène « map » avec « route » : "
                              f"{{\"focus\": \"world\", \"places\": [{places}], \"route\": {route}}}")))
    talk = [_body_hits(_say(s)) for s in scenes]
    talking = [(parts, posts) for parts, posts in talk if parts or posts]
    if len(talking) >= BODY_MIN_SCENES and not any(s.get("type") == "body" for s in scenes):
        cited: dict = {}
        for parts, _ in talking:
            for part in parts:
                cited[part] = cited.get(part, 0) + 1
        top = sorted(cited, key=lambda p: -cited[p])[:BODY_MAX_MARKS]
        marks = ", ".join(json.dumps({"part": p}) for p in top)
        out.append((2, *_line("corps-sans-dessin", where, f"{len(talking)} scènes parlent du corps ou d'une posture sans scène « body »",
                              f"Ajoute une scène « body » : {{\"pose\": \"{_pose_for(scenes)}\", \"marks\": [{marks}]}}")))
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
        _part_findings(part, part["n"], scored, plan.get("lang") or "fr")
    total = sum(len(p["scenes"]) for p in plan["parts"])
    if seconds and total / (seconds / 60) > MAX_SCENES_PER_MINUTE:
        scored.append((1, *_line("rythme-hache", "Plan", f"{total} scènes pour environ {seconds} s, plus de {MAX_SCENES_PER_MINUTE} scènes par minute (rythme haché)",
                                "Fusionne des scènes ou allonge les « say »")))
    info = plan_check.read_json(job, "info.json", {})
    duration = info.get("duration") if isinstance(info, dict) else None
    if isinstance(duration, (int, float)) and not isinstance(duration, bool) and duration > 0:
        _, ranges = plan_check.sponsor_ranges(job, info)
        low, _ = target.bounds(target.useful_seconds(float(duration), ranges))
        if seconds < SURVEY_MINIMUM_SHARE * low and _coverage(plan, float(duration)) > SURVEY_SHARE:
            scored.append((1, *_line("survol", "Plan", f"durée estimée {seconds} s, bien sous les {low} s conseillés, alors que les « src » couvrent plus de {round(SURVEY_SHARE * 100)} % de la source",
                                    "Tu survoles toute la source : garde moins de sujets et explique bien chacun, une vidéo courte convient")))
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
