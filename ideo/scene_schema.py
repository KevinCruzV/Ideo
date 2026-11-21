import re

TEXT = "text"
NUMBER = "number"
LABEL = "label"
OPTIONAL_TEXT = "optional-text"
OBJECTS = ("screen", "board", "jar", "door", "scale")
GRID_SHAPES = ("circle", "square", "triangle", "diamond", "arrow", "strip")
DIAGRAM_SHAPES = ("circle", "square", "triangle", "bar")


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
        "required": {"cells": object_list(9, {"shape": GRID_SHAPES, "label": TEXT}, ("label",))},
        "optional": {},
        "el": ("cells.<i>",),
    },
    "stamp": {"required": {"text": TEXT}, "optional": {}, "el": ("text",)},
    "quote": {"required": {"text": TEXT}, "optional": {"speaker": OPTIONAL_TEXT}, "el": ("text", "speaker")},
    "object-state": {"required": {"object": OBJECTS, "states": text_list(6)}, "optional": {}, "el": ("states.<i>",)},
    "shape-diagram": {
        "required": {"values": number_list(8)},
        "optional": {"shape": DIAGRAM_SHAPES, "labels": text_list(8)},
        "el": ("values.<i>", "labels.<i>"),
    },
    "mascot": {"required": {"bubble": TEXT}, "optional": {}, "el": ("bubble",)},
}

INDEXED = re.compile(r"^([a-z]+)\.(\d+)$")


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
    return errors


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
    valid = isinstance(el, str) and el in SCHEMA[kind]["el"]
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
