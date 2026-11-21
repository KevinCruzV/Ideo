import math
import re
import unicodedata

TEXT = "text"
NUMBER = "number"
LABEL = "label"
OPTIONAL_TEXT = "optional-text"
OBJECTS = ("screen", "board", "jar", "door", "scale")
GRID_SHAPES = ("circle", "square", "triangle", "diamond", "arrow", "strip")
DIAGRAM_SHAPES = ("circle", "square", "triangle", "bar")
MASCOT_POSES = ("question", "surprise", "montre", "content")
PICTOS = (
    "globe", "flag", "pin", "city", "house", "factory", "bank", "coin", "chart-up", "chart-down", "ship", "plane",
    "train", "rocket", "satellite", "tank", "shield", "sword", "bomb", "dove", "handshake", "justice", "wall", "chain",
    "lock", "key", "crown", "ballot", "megaphone", "newspaper", "tv", "phone", "computer", "chip", "book", "brain",
    "heart", "eye", "clock", "calendar", "lightbulb", "atom", "flask", "leaf", "sun", "drop", "fire", "lightning",
    "mountain", "barrel", "gear", "people",
)
PICTO_KINDS = ("key-title", "fact-chips", "stack-list", "counter", "timeline", "stamp", "quote")
KICKER_CAP = 28


def text_list(most: int) -> dict:
    return {"list": TEXT, "max": most}


def number_list(most: int) -> dict:
    return {"list": NUMBER, "max": most}


def object_list(most: int, keys: dict, required: tuple) -> dict:
    return {"list": "object", "max": most, "keys": keys, "required": required}


SCHEMA = {
    "key-title": {"required": {"text": TEXT}, "optional": {"accent": TEXT}, "el": ("text", "accent")},
    "person-card": {"required": {"name": TEXT}, "optional": {"role": TEXT}, "el": ("avatar", "name", "role")},
    "fact-chips": {"required": {"chips": text_list(6)}, "optional": {}, "el": ("chips.<i>",)},
    "stack-list": {"required": {"items": text_list(5)}, "optional": {}, "el": ("items.<i>",)},
    "counter": {"required": {"to": NUMBER}, "optional": {"from": NUMBER, "label": TEXT}, "el": ("to", "label")},
    "timeline": {
        "required": {"marks": object_list(5, {"at": LABEL, "label": TEXT}, ("at",))},
        "optional": {"start": LABEL, "end": LABEL},
        "el": ("marks.<i>",),
    },
    "icon-grid": {
        "required": {"cells": object_list(9, {"shape": GRID_SHAPES, "label": TEXT, "picto": PICTOS}, ("label",))},
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
    "versus": {
        "required": {"left": TEXT, "right": TEXT},
        "optional": {"left_picto": PICTOS, "right_picto": PICTOS},
        "el": ("left", "right"),
    },
}
for _kind, _schema in SCHEMA.items():
    _schema["optional"]["kicker"] = TEXT
    if _kind in PICTO_KINDS:
        _schema["optional"]["picto"] = PICTOS

PART_CAPS = {"hook": 60, "title": 40}
TEXT_CAPS = {
    "key-title": {"text": 90, "accent": 40},
    "person-card": {"name": 48, "role": 100},
    "fact-chips": {"chips": 28},
    "stack-list": {"items": 60},
    "counter": {"label": 60},
    "timeline": {"marks.at": 12, "marks.label": 48, "start": 30, "end": 30},
    "icon-grid": {"cells.label": 16},
    "stamp": {"text": 48},
    "quote": {"text": 200, "speaker": 32},
    "object-state": {"states": 36},
    "shape-diagram": {"labels": 14},
    "mascot": {"bubble": 80},
    "versus": {"left": 24, "right": 24},
}
for _kind, _fields in TEXT_CAPS.items():
    _fields["kicker"] = KICKER_CAP
TEXT_CAPS["shape-diagram"]["unit"] = 8
CHARS_PER_WORD = 6

INDEXED = re.compile(r"^([a-z]+)\.(\d+)$")
NOT_WORD = re.compile(r"[\W_]+")


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
    if isinstance(spec, tuple):
        return "une de ces valeurs : " + ", ".join(spec)
    if spec["list"] == TEXT:
        return f"une liste de 1 à {spec['max']} textes"
    if spec["list"] == NUMBER:
        return f"une liste de 1 à {spec['max']} nombres"
    keys = ", ".join(f"« {k} »" for k in spec["keys"])
    return f"une liste de 1 à {spec['max']} objets avec {keys}"


def _valid(spec, value) -> bool:
    if spec == TEXT:
        return isinstance(value, str) and bool(value.strip())
    if spec == NUMBER:
        return _is_number(value)
    if spec == OPTIONAL_TEXT:
        return isinstance(value, str)
    if spec == LABEL:
        return (isinstance(value, str) and bool(value.strip())) or _is_number(value)
    if isinstance(spec, tuple):
        return value in spec
    if not isinstance(value, list) or not 1 <= len(value) <= spec["max"]:
        return False
    if spec["list"] in (TEXT, NUMBER):
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
    for key, spec in known.items():
        if key in props and not _valid(spec, props[key]):
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
