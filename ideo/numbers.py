import re
from dataclasses import dataclass

from num2words import num2words

from ideo import align

COVERED = ("fr", "en", "es", "de", "it", "pt", "nl", "pl")
YEAR_FORM = ("en", "de", "nl")
YEAR_MIN, YEAR_MAX = 1100, 2099
LIMIT = 10 ** 12
PERCENT = {"fr": "pour cent", "en": "percent", "es": "por ciento", "de": "Prozent", "it": "per cento", "pt": "por cento",
           "nl": "procent", "pl": "procent"}
FR_YEAR_CONTEXT = frozenset({"en", "depuis", "des", "dès", "vers", "avant", "apres", "après", "puis", "entre", "an", "annee",
                             "année", "jusqu'en"})
CURRENCY = {
    "fr": {"€": ("euro", "euros"), "$": ("dollar", "dollars")},
    "en": {"€": ("euro", "euros"), "$": ("dollar", "dollars")},
}
UNITS = {
    "fr": {"cm": ("centimètre", "centimètres"), "mm": ("millimètre", "millimètres"), "km": ("kilomètre", "kilomètres"),
           "kg": ("kilogramme", "kilogrammes"), "Md$": ("milliard de dollars", "milliards de dollars"),
           "M$": ("million de dollars", "millions de dollars"), "Md€": ("milliard d'euros", "milliards d'euros"),
           "M€": ("million d'euros", "millions d'euros"), "km/h": ("kilomètre par heure", "kilomètres par heure"),
           "°C": ("degré Celsius", "degrés Celsius")},
    "en": {"cm": ("centimeter", "centimeters"), "mm": ("millimeter", "millimeters"), "km": ("kilometer", "kilometers"),
           "kg": ("kilogram", "kilograms"), "km/h": ("kilometer per hour", "kilometers per hour"),
           "°C": ("degree Celsius", "degrees Celsius")},
}
FR_ORDINAL = re.compile(r"^(er|re|ère|e|ème|nd|nde|d)$")
EN_ORDINAL = re.compile(r"^(st|nd|rd|th)$")
TOKEN = re.compile(r"^(?P<pre>[«\u00a0\"“(\[‘']*)(?P<num>\d[\d.,]*\d|\d)(?P<suf>[%€$]?)(?P<ord>[a-zèé]{1,3})?(?P<post>[^\w%€$]*)$")
GROUP = re.compile(r"^(?P<num>\d{3})(?P<post>[^\w%€$]*)$")
HEAD = re.compile(r"^\d{1,3}$")


@dataclass
class Normalized:
    text: str
    units: list | None


def _spell(value, lang: str, **kw) -> str | None:
    try:
        words = num2words(value, lang=lang, **kw)
    except (NotImplementedError, OverflowError, ValueError, KeyError):
        return None
    return " ".join(words.replace(",", " ").split()) if words else None


def parse(raw: str, lang: str):
    if re.fullmatch(r"\d+", raw):
        if len(raw) > 1 and raw.startswith("0") or int(raw) >= LIMIT:
            return None
        return int(raw)
    if lang == "en":
        if re.fullmatch(r"\d{1,3}(,\d{3})+", raw):
            return int(raw.replace(",", ""))
        if re.fullmatch(r"\d+\.\d+", raw):
            return float(raw)
        return None
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", raw):
        return int(raw.replace(".", ""))
    if re.fullmatch(r"\d+[,.]\d+", raw):
        return float(raw.replace(",", "."))
    return None


def cardinal(value, lang: str, year: bool = False, context: str = "") -> str | None:
    if isinstance(value, float):
        return _spell(value, lang)
    if year and lang in YEAR_FORM and YEAR_MIN <= value <= YEAR_MAX:
        words = _spell(value, lang, to="year")
        if words:
            return words
    words = _spell(value, lang)
    if words and lang == "fr" and YEAR_MIN <= value <= YEAR_MAX and context in FR_YEAR_CONTEXT:
        words = re.sub(r"\bcents$", "cent", words)
        words = re.sub(r"\bvingts$", "vingt", words)
    return words


def ordinal(value: int, suffix: str, lang: str, feminine: bool = False) -> str | None:
    if lang == "fr" and FR_ORDINAL.match(suffix):
        if value == 1:
            return "première" if feminine or suffix in ("re", "ère") else "premier"
        if value == 2 and suffix in ("nd", "nde", "d"):
            return "seconde" if suffix == "nde" else "second"
        if suffix in ("er", "re", "ère", "nd", "nde", "d"):
            return None
        return _spell(value, "fr", to="ordinal")
    if lang == "en" and EN_ORDINAL.match(suffix):
        return _spell(value, "en", to="ordinal")
    return None


def _decorate(words: list[str], pre: str, post: str) -> list[str]:
    words = list(words)
    words[0] = pre + words[0]
    words[-1] = words[-1] + post
    return words


def _unit_key(token: str) -> tuple[str, str] | None:
    match = re.match(r"^(?P<unit>.*?)(?P<post>[.,;:!?…»”\")\]]*)$", token)
    return (match.group("unit"), match.group("post")) if match else None


def _convert(words: list[str], i: int, lang: str) -> tuple[list[str], int] | None:
    token = words[i]
    consumed = 1
    match = TOKEN.match(token)
    if match is None:
        return None
    pre, raw, suf, ending, post = (match.group(k) for k in ("pre", "num", "suf", "ord", "post"))
    if HEAD.match(raw) and not suf and not ending and not post and not pre:
        j = i + 1
        groups = []
        while j < len(words) and GROUP.match(words[j]):
            groups.append(GROUP.match(words[j]))
            j += 1
            if groups[-1].group("post"):
                break
        if groups and all(not g.group("post") for g in groups[:-1]):
            raw = raw + "".join(g.group("num") for g in groups)
            post = groups[-1].group("post")
            consumed = 1 + len(groups)
    value = parse(raw, lang)
    if value is None:
        return None
    previous = re.sub(r"[^\w']", "", words[i - 1].lower()) if i else ""
    if ending:
        if suf or not isinstance(value, int) or consumed > 1:
            return None
        spoken = ordinal(value, ending, lang)
        return (_decorate(spoken.split(), pre, post), 1) if spoken else None
    year = len(raw) == 4 and consumed == 1 and isinstance(value, int)
    spoken = cardinal(value, lang, year=year, context=previous)
    if not spoken:
        return None
    result = spoken.split()
    if suf == "%":
        phrase = PERCENT.get(lang)
        if not phrase:
            return None
        return _decorate(result + phrase.split(), pre, post), consumed
    if suf in ("€", "$"):
        names = CURRENCY.get(lang, {}).get(suf)
        if not names:
            return None
        unit = names[0] if value == 1 else names[1]
        return _decorate(result + unit.split(), pre, post), consumed
    nxt = words[i + consumed] if i + consumed < len(words) else None
    key = _unit_key(nxt) if nxt else None
    table = UNITS.get(lang, {})
    if key and key[0] in table and not post:
        singular, plural = table[key[0]]
        unit = singular if value == 1 else plural
        return _decorate(result + unit.split(), pre, key[1]), consumed + 1
    return _decorate(result, pre, post), consumed


def normalize(text: str, lang: str) -> Normalized:
    if lang not in COVERED or not re.search(r"\d", text):
        return Normalized(text, None)
    words = align.script_words(text)
    units: list = []
    spoken: list[str] = []
    changed = False
    i = 0
    while i < len(words):
        converted = _convert(words, i, lang)
        if converted:
            said, used = converted
            units.append({"orig": used, "said": len(said), "numeric": True})
            spoken.extend(said)
            changed = True
            i += used
        else:
            units.append({"orig": 1, "said": 1, "numeric": False})
            spoken.append(words[i])
            i += 1
    if not changed:
        return Normalized(text, None)
    return Normalized(" ".join(spoken).replace(align.NBSP, " "), units)


def plain_words(spoken: str, units: list | None) -> str:
    if not units:
        return spoken
    words = spoken.split()
    out, k = [], 0
    for unit in units:
        chunk = words[k:k + unit["said"]]
        k += unit["said"]
        if not unit["numeric"]:
            out.extend(chunk)
    return " ".join(out)
