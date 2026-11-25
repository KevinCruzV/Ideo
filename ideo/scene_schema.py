import math
import re
import unicodedata

TIMELINE_PROPS = frozenset({"variant"})
TEXT = "text"
NUMBER = "number"
LABEL = "label"
OPTIONAL_TEXT = "optional-text"
PICTO = "picto"
MAP_CODE = "map-code"
BOOL = "bool"
OBJECTS = ("screen", "board", "jar", "door", "scale", "phone")
GRID_SHAPES = ("circle", "square", "triangle", "diamond", "arrow", "strip")
DIAGRAM_SHAPES = ("circle", "square", "triangle", "bar")
MASCOT_POSES = ("question", "surprise", "montre", "content")
PICTOS = (
    "globe", "flag", "pin", "city", "house", "factory", "bank", "coin", "chart-up", "chart-down", "ship", "plane",
    "train", "rocket", "satellite", "tank", "shield", "sword", "bomb", "dove", "handshake", "justice", "wall", "chain",
    "lock", "key", "crown", "ballot", "megaphone", "newspaper", "tv", "phone", "computer", "chip", "book", "brain",
    "heart", "eye", "clock", "calendar", "lightbulb", "atom", "flask", "leaf", "sun", "drop", "fire", "lightning",
    "mountain", "barrel", "gear", "people",
    "lungs", "stomach", "spine", "bone", "muscle", "tooth", "blood", "pill", "syringe", "virus", "bed", "pillow", "moon",
    "thermometer", "scale-weight", "apple", "dumbbell", "running-shoe", "stethoscope", "hospital",
    "raised-bed", "stomach-sleeper", "knee-pillow", "snore", "pelvis-tilt", "numb-arm",
    "blood-stain", "chalk-outline", "crime-tape", "handcuffs", "knife", "coffin", "tombstone",
    "mirror", "mars",
)
FLAGS = (
    "ad", "ae", "af", "ag", "ai", "al", "am", "ao", "aq", "ar", "as", "at", "au", "aw", "ax", "az", "ba", "bb",
    "bd", "be", "bf", "bg", "bh", "bi", "bj", "bl", "bm", "bn", "bo", "bq", "br", "bs", "bt", "bv", "bw", "by",
    "bz", "ca", "cc", "cd", "cf", "cg", "ch", "ci", "ck", "cl", "cm", "cn", "co", "cr", "cu", "cv", "cw", "cx",
    "cy", "cz", "de", "dj", "dk", "dm", "do", "dz", "ec", "ee", "eg", "eh", "er", "es", "et", "eu", "fi", "fj",
    "fk", "fm", "fo", "fr", "ga", "gb", "gd", "ge", "gf", "gg", "gh", "gi", "gl", "gm", "gn", "gp", "gq", "gr",
    "gs", "gt", "gu", "gw", "gy", "hk", "hm", "hn", "hr", "ht", "hu", "id", "ie", "il", "im", "in", "io", "iq",
    "ir", "is", "it", "je", "jm", "jo", "jp", "ke", "kg", "kh", "ki", "km", "kn", "kp", "kr", "kw", "ky", "kz",
    "la", "lb", "lc", "li", "lk", "lr", "ls", "lt", "lu", "lv", "ly", "ma", "mc", "md", "me", "mf", "mg", "mh",
    "mk", "ml", "mm", "mn", "mo", "mp", "mq", "mr", "ms", "mt", "mu", "mv", "mw", "mx", "my", "mz", "na", "nc",
    "ne", "nf", "ng", "ni", "nl", "no", "np", "nr", "nu", "nz", "om", "pa", "pe", "pf", "pg", "ph", "pk", "pl",
    "pm", "pn", "pr", "ps", "pt", "pw", "py", "qa", "re", "ro", "rs", "ru", "rw", "sa", "sb", "sc", "sd", "se",
    "sg", "sh", "si", "sj", "sk", "sl", "sm", "sn", "so", "sr", "ss", "st", "su", "sv", "sx", "sy", "sz", "tc",
    "td", "tf", "tg", "th", "tj", "tk", "tl", "tm", "tn", "to", "tr", "tt", "tv", "tw", "tz", "ua", "ug", "um",
    "un", "us", "uy", "uz", "va", "vc", "ve", "vg", "vi", "vn", "vu", "wf", "ws", "ye", "yt", "za", "zm", "zw",
)
REGION_FLAGS = ("es-ct", "gb-eng", "gb-nir", "gb-sct", "gb-wls")
MAP_CODES = (
    "ad", "ae", "af", "ag", "ai", "al", "am", "ao", "aq", "ar", "as", "at", "au", "aw", "ax", "az", "ba", "bb",
    "bd", "be", "bf", "bg", "bh", "bi", "bj", "bl", "bm", "bn", "bo", "br", "bs", "bt", "bw", "by", "bz", "ca",
    "cd", "cf", "cg", "ch", "ci", "ck", "cl", "cm", "cn", "co", "cr", "cu", "cv", "cw", "cy", "cz", "de", "dj",
    "dk", "dm", "do", "dz", "ec", "ee", "eg", "eh", "er", "es", "et", "fi", "fj", "fk", "fm", "fo", "fr", "ga",
    "gb", "gd", "ge", "gg", "gh", "gl", "gm", "gn", "gq", "gr", "gs", "gt", "gu", "gw", "gy", "hk", "hm", "hn",
    "hr", "ht", "hu", "id", "ie", "il", "im", "in", "io", "iq", "ir", "is", "it", "je", "jm", "jo", "jp", "ke",
    "kg", "kh", "ki", "km", "kn", "kp", "kr", "kw", "ky", "kz", "la", "lb", "lc", "li", "lk", "lr", "ls", "lt",
    "lu", "lv", "ly", "ma", "mc", "md", "me", "mf", "mg", "mh", "mk", "ml", "mm", "mn", "mo", "mp", "mr", "ms",
    "mt", "mu", "mv", "mw", "mx", "my", "mz", "na", "nc", "ne", "nf", "ng", "ni", "nl", "no", "np", "nr", "nu",
    "nz", "om", "pa", "pe", "pf", "pg", "ph", "pk", "pl", "pm", "pn", "pr", "ps", "pt", "pw", "py", "qa", "ro",
    "rs", "ru", "rw", "sa", "sb", "sc", "sd", "se", "sg", "sh", "si", "sk", "sl", "sm", "sn", "so", "sr", "ss",
    "st", "sv", "sx", "sy", "sz", "tc", "td", "tf", "tg", "th", "tj", "tl", "tm", "tn", "to", "tr", "tt", "tw",
    "tz", "ua", "ug", "us", "uy", "uz", "va", "vc", "ve", "vg", "vi", "vn", "vu", "wf", "ws", "ye", "za", "zm",
    "zw",
)
MAP_FOCUS = ("world", "europe", "africa", "asia", "north-america", "south-america", "middle-east", "oceania", "arctic")
BODY_POSES = ("standing", "sitting", "walking", "running", "lying-back", "lying-starfish", "lying-side-left",
              "lying-side-right", "lying-fetal", "lying-stomach")
BODY_SETTINGS = ("none", "bed", "chair", "desk", "outdoor")
BODY_PARTS = ("head", "brain", "neck", "throat", "shoulders", "chest", "heart", "lungs", "stomach", "back", "spine", "hips",
              "arms", "hands", "knees", "legs", "feet")
BODY_TONES = ("good", "bad", "neutral")
PICTO_KINDS = ("key-title", "person-card", "fact-chips", "stack-list", "counter", "timeline", "stamp", "quote")
FLAG_EXAMPLES = ("fr", "us", "cn", "de", "br", "za")
HAIRS = ("none", "short", "side", "long", "curly", "wild", "bun", "crown-bald")
HAIR_COLORS = ("black", "brown", "blond", "red", "grey", "white")
FACIALS = ("none", "moustache", "beard", "goatee", "sideburns")
HATS = ("none", "cap", "kepi", "bicorne", "crown", "helmet", "top-hat", "beret", "turban", "laurel", "wig")
OUTFITS = ("suit", "uniform", "robe", "lab-coat", "casual", "toga", "armor", "dress")
SKINS = ("light", "tan", "brown", "dark")
GENDERS = ("woman", "man")
AGES = ("child", "adult", "old")
JOBS = ("police", "firefighter", "doctor", "judge", "soldier", "worker", "journalist", "lawyer")
KICKER_CAP = 28


def text_list(most: int) -> dict:
    return {"list": TEXT, "max": most}


def number_list(most: int) -> dict:
    return {"list": NUMBER, "max": most}


def object_list(most: int, keys: dict, required: tuple, least: int = 1) -> dict:
    return {"list": "object", "max": most, "min": least, "keys": keys, "required": required}


def code_list(most: int, least: int) -> dict:
    return {"list": MAP_CODE, "max": most, "min": least}


SCHEMA = {
    "key-title": {"required": {"text": TEXT}, "optional": {"accent": TEXT}, "el": ("text", "accent")},
    "person-card": {
        "required": {"name": TEXT},
        "optional": {"role": TEXT, "hair": HAIRS, "hair_color": HAIR_COLORS, "facial": FACIALS, "hat": HATS,
                     "glasses": BOOL, "outfit": OUTFITS, "skin": SKINS, "gender": GENDERS, "age": AGES, "job": JOBS,
                     "photo": BOOL},
        "el": ("avatar", "name", "role"),
    },
    "fact-chips": {"required": {"chips": text_list(6)}, "optional": {}, "el": ("chips.<i>",)},
    "stack-list": {"required": {"items": text_list(5)}, "optional": {}, "el": ("items.<i>",)},
    "counter": {"required": {"to": NUMBER}, "optional": {"from": NUMBER, "label": TEXT, "unit": TEXT}, "el": ("to", "label")},
    "timeline": {
        "required": {"marks": object_list(5, {"at": LABEL, "label": TEXT}, ("at",))},
        "optional": {"start": LABEL, "end": LABEL},
        "el": ("marks.<i>",),
    },
    "icon-grid": {
        "required": {"cells": object_list(9, {"shape": GRID_SHAPES, "label": TEXT, "picto": PICTO}, ("label",))},
        "optional": {},
        "el": ("cells.<i>",),
    },
    "stamp": {"required": {"text": TEXT}, "optional": {}, "el": ("text",)},
    "quote": {"required": {"text": TEXT}, "optional": {"speaker": OPTIONAL_TEXT}, "el": ("text", "speaker")},
    "object-state": {"required": {"object": OBJECTS, "states": text_list(6)}, "optional": {}, "el": ("states.<i>",)},
    "shape-diagram": {
        "required": {"values": number_list(8)},
        "optional": {"shape": DIAGRAM_SHAPES, "labels": text_list(8), "unit": TEXT},
        "el": ("values.<i>", "labels.<i>"),
    },
    "mascot": {"required": {"bubble": TEXT}, "optional": {"pose": MASCOT_POSES}, "el": ("bubble",)},
    "map": {
        "required": {"focus": MAP_FOCUS, "places": object_list(6, {"code": MAP_CODE, "label": TEXT}, ("code",))},
        "optional": {"route": code_list(6, 2)},
        "el": ("places.<i>", "route"),
    },
    "body": {
        "required": {"pose": BODY_POSES},
        "optional": {"setting": BODY_SETTINGS, "tone": BODY_TONES,
                     "marks": object_list(4, {"part": BODY_PARTS, "label": TEXT}, ("part",), least=0)},
        "el": ("marks.<i>",),
    },
    "versus": {
        "required": {"left": TEXT, "right": TEXT},
        "optional": {"left_picto": PICTO, "right_picto": PICTO},
        "el": ("left", "right"),
    },
}
for _kind, _schema in SCHEMA.items():
    _schema["optional"]["kicker"] = TEXT
    if _kind in PICTO_KINDS:
        _schema["optional"]["picto"] = PICTO

PART_CAPS = {"hook": 60, "title": 40, "question": 60}
TEXT_CAPS = {
    "key-title": {"text": 90, "accent": 40},
    "person-card": {"name": 48, "role": 100},
    "fact-chips": {"chips": 28},
    "stack-list": {"items": 60},
    "counter": {"label": 60, "unit": 4},
    "timeline": {"marks.at": 12, "marks.label": 48, "start": 30, "end": 30},
    "icon-grid": {"cells.label": 16},
    "stamp": {"text": 48},
    "quote": {"text": 200, "speaker": 32},
    "object-state": {"states": 36},
    "shape-diagram": {"labels": 14},
    "mascot": {"bubble": 80},
    "versus": {"left": 24, "right": 24},
    "map": {"places.label": 24},
    "body": {"marks.label": 28},
}
for _kind, _fields in TEXT_CAPS.items():
    _fields["kicker"] = KICKER_CAP
TEXT_CAPS["shape-diagram"]["unit"] = 8
CHARS_PER_WORD = 6

INDEXED = re.compile(r"^([a-z]+)\.(\d+)$")
NOT_WORD = re.compile(r"[\W_]+")


FLAG_PREFIX = "flag:"


def is_flag(value) -> bool:
    return isinstance(value, str) and value.startswith(FLAG_PREFIX) and value[len(FLAG_PREFIX):] in FLAGS + REGION_FLAGS


def _flag_problems(props: dict) -> list[tuple[str, str]]:
    found = []
    for key in ("picto", "left_picto", "right_picto"):
        value = props.get(key)
        if isinstance(value, str) and value.startswith(FLAG_PREFIX) and not is_flag(value):
            found.append((f"props.{key}", value))
    cells = props.get("cells")
    for i, cell in enumerate(cells if isinstance(cells, list) else []):
        value = cell.get("picto") if isinstance(cell, dict) else None
        if isinstance(value, str) and value.startswith(FLAG_PREFIX) and not is_flag(value):
            found.append((f"props.cells.{i}.picto", value))
    return found


def _map_problems(kind: str, props: dict) -> list[tuple[str, str]]:
    if kind != "map":
        return []
    found = []
    places = props.get("places")
    for i, place in enumerate(places if isinstance(places, list) else []):
        code = place.get("code") if isinstance(place, dict) else None
        if isinstance(code, str) and code not in MAP_CODES:
            found.append((f"props.places.{i}.code", code))
    route = props.get("route")
    for i, code in enumerate(route if isinstance(route, list) else []):
        if isinstance(code, str) and code not in MAP_CODES:
            found.append((f"props.route.{i}", code))
    return found


def _map_neutral(value, bad: set):
    if isinstance(value, str) and value in bad:
        return "fr"
    if isinstance(value, list):
        return [_map_neutral(v, bad) for v in value]
    if isinstance(value, dict):
        return {k: _map_neutral(v, bad) for k, v in value.items()}
    return value


def _neutral(value):
    if isinstance(value, str) and value.startswith(FLAG_PREFIX) and not is_flag(value):
        return PICTOS[0]
    if isinstance(value, list):
        return [_neutral(v) for v in value]
    if isinstance(value, dict):
        return {k: _neutral(v) for k, v in value.items()}
    return value


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _describe(spec) -> str:
    if spec == TEXT:
        return "un texte non vide"
    if spec == NUMBER:
        return "un nombre (sans guillemets ni unité)"
    if spec == LABEL:
        return "un texte ou un nombre"
    if spec == OPTIONAL_TEXT:
        return "un texte, vide si inconnu"
    if spec == PICTO:
        return ("un des dessins " + ", ".join(PICTOS) + ", ou un drapeau « flag:<code> » avec un code de pays à deux lettres "
                "en minuscules (par exemple flag:fr)")
    if spec == BOOL:
        return "true ou false, sans guillemets"
    if isinstance(spec, tuple):
        return "une de ces valeurs : " + ", ".join(spec)
    least = spec.get("min", 1)
    if spec == MAP_CODE:
        return "un code de pays à deux lettres en minuscules, comme cn, ru ou in"
    if spec["list"] == TEXT:
        return f"une liste de 1 à {spec['max']} textes"
    if spec["list"] == NUMBER:
        return f"une liste de 1 à {spec['max']} nombres"
    if spec["list"] == MAP_CODE:
        return f"une liste de {least} à {spec['max']} codes de pays à deux lettres en minuscules, comme cn, ru ou in"
    keys = ", ".join(f"« {k} »" for k in spec["keys"])
    return f"une liste de {least} à {spec['max']} objets avec {keys}"


def _valid(spec, value) -> bool:
    if spec == TEXT:
        return isinstance(value, str) and bool(value.strip())
    if spec == NUMBER:
        return _is_number(value)
    if spec == OPTIONAL_TEXT:
        return isinstance(value, str)
    if spec == LABEL:
        return (isinstance(value, str) and bool(value.strip())) or _is_number(value)
    if spec == PICTO:
        return isinstance(value, str) and (value in PICTOS or is_flag(value))
    if spec == BOOL:
        return isinstance(value, bool)
    if spec == MAP_CODE:
        return isinstance(value, str) and value in MAP_CODES
    if isinstance(spec, tuple):
        return value in spec
    if not isinstance(value, list) or not spec.get("min", 1) <= len(value) <= spec["max"]:
        return False
    if spec["list"] in (TEXT, NUMBER, MAP_CODE):
        return all(_valid(spec["list"], v) for v in value)
    for entry in value:
        if not isinstance(entry, dict) or set(entry) - set(spec["keys"]):
            return False
        if any(k not in entry for k in spec["required"]):
            return False
        if any(not _valid(spec["keys"][k], v) for k, v in entry.items()):
            return False
    return True


def bare_words(text: str) -> list[str]:
    return [w for w in (NOT_WORD.sub("", part.lower()) for part in text.split(" ")) if w]


def accent_in_text(text: str, accent: str) -> bool:
    words, wanted = bare_words(text), bare_words(accent)
    if not wanted:
        return False
    return any(words[i:i + len(wanted)] == wanted for i in range(len(words) - len(wanted) + 1))


def _coherence(kind: str, props: dict, where: str) -> list[str]:
    if kind == "shape-diagram":
        values, labels = props.get("values"), props.get("labels")
        if (_valid(SCHEMA[kind]["required"]["values"], values) and _valid(SCHEMA[kind]["optional"]["labels"], labels)
                and len(values) != len(labels)):
            return [f"{where} : « props.labels » a {len(labels)} textes et « props.values » {len(values)} nombres : "
                    "donne autant de « labels » que de « values », sinon les étiquettes ne s'affichent pas."]
    if kind == "key-title":
        text, accent = props.get("text"), props.get("accent")
        if _valid(TEXT, text) and _valid(TEXT, accent) and not accent_in_text(text, accent):
            return [f"{where} : « props.accent » « {accent} » n'est pas un mot de « props.text ». "
                    "Recopie un mot ou une suite de mots exacts de « text »."]
    return []


def flat_caps() -> dict:
    caps = dict(PART_CAPS)
    for kind, fields in TEXT_CAPS.items():
        caps.update({f"{kind}.{path}": cap for path, cap in fields.items()})
    return caps


def screen_length(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def cap_error(where: str, field: str, text: str, cap: int) -> str | None:
    length = screen_length(text.strip())
    if length <= cap:
        return None
    words = max(1, math.ceil((length - cap) / CHARS_PER_WORD))
    return (f"{where} : « {field} » fait {length} caractères, {cap} au plus à l'écran : "
            f"raccourcis-le d'environ {words} mot{'s' if words > 1 else ''}, sinon le texte est coupé.")


def _capped(props: dict, path: str):
    name, _, key = path.partition(".")
    value = props.get(name)
    if not key:
        if isinstance(value, list):
            yield from ((f"props.{name}.{i}", v) for i, v in enumerate(value))
        else:
            yield f"props.{name}", value
        return
    for i, entry in enumerate(value if isinstance(value, list) else []):
        if isinstance(entry, dict) and key in entry:
            yield f"props.{name}.{i}.{key}", entry[key]


def _caps(kind: str, props: dict, where: str) -> list[str]:
    errors = []
    for path, cap in TEXT_CAPS[kind].items():
        for field, value in _capped(props, path):
            if _is_number(value):
                value = str(value)
            if isinstance(value, str):
                error = cap_error(where, field, value, cap)
                if error:
                    errors.append(error)
    return errors


def accepted_props(kind: str) -> str:
    schema = SCHEMA[kind]
    return ", ".join(list(schema["required"]) + list(schema["optional"]))


def check_props(kind: str, props: dict, where: str) -> list[str]:
    schema = SCHEMA[kind]
    known = {**schema["required"], **schema["optional"]}
    errors = []
    for key in props:
        if key not in known:
            errors.append(f"{where} : prop inconnue « {key} » pour « {kind} ». Props acceptées : {accepted_props(kind)}.")
    for key in schema["required"]:
        if key not in props:
            errors.append(f"{where} : prop « {key} » manquante pour « {kind} ». Props acceptées : {accepted_props(kind)}.")
    map_problems = _map_problems(kind, props)
    bad_codes = {code for _, code in map_problems}
    for field, value in map_problems:
        errors.append(f"{where} : « {field} » : « {value} » n'a pas de contour sur la carte. Écris un code de pays à deux lettres "
                      "en minuscules (par exemple cn, ru, in). Quelques petits territoires (par exemple gf, re, yt) et eu, un, su "
                      "n'ont pas de contour : choisis un autre pays.")
    problems = _flag_problems(props)
    for field, value in problems:
        errors.append(f"{where} : « {field} » : « {value} » n'est pas un drapeau connu. Écris « flag: » suivi d'un code de pays "
                      f"à deux lettres en minuscules, par exemple {', '.join(FLAG_PREFIX + c for c in FLAG_EXAMPLES)}.")
    for key, spec in known.items():
        if key in props and not _valid(spec, props[key]):
            if problems and _valid(spec, _neutral(props[key])):
                continue
            if bad_codes and _valid(spec, _map_neutral(props[key], bad_codes)):
                continue
            errors.append(f"{where} : « props.{key} » doit être {_describe(spec)}.")
    return errors + _coherence(kind, props, where) + _caps(kind, props, where)


def el_paths(kind: str, props: dict) -> list[str]:
    out = []
    for pattern in SCHEMA[kind]["el"]:
        if not pattern.endswith(".<i>"):
            out.append(pattern)
            continue
        name = pattern[:-4]
        values = props.get(name)
        count = len(values) if isinstance(values, list) else 0
        if count:
            out.append(f"{name}.0 à {name}.{count - 1}")
    return out


def check_el(kind: str, props: dict, el, where: str) -> list[str]:
    valid = isinstance(el, str) and el in SCHEMA[kind]["el"] and not el.endswith(".<i>")
    if isinstance(el, str):
        match = INDEXED.match(el)
        if match and f"{match.group(1)}.<i>" in SCHEMA[kind]["el"]:
            values = props.get(match.group(1))
            count = len(values) if isinstance(values, list) else 0
            valid = int(match.group(2)) < count
    if valid:
        return []
    paths = ", ".join(el_paths(kind, props)) or "aucun"
    return [f"{where} : « el » « {el} » invalide pour « {kind} ». Chemins acceptés : {paths}."]
