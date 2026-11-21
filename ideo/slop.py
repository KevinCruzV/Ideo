import re

from ideo import countries

KNOWN_ACRONYMS = frozenset({
    "OTAN", "BRICS", "ONU", "NASA", "NATO", "OPEP", "OPEC", "ASEAN", "CNRS", "INSEE", "SIDA", "COVID", "ADN", "UNICEF",
})
ROMAN = re.compile(r"^[IVXLCDM]+$")
DASH = re.compile("[\u2013\u2014]|--|(?<=\\s)[-\u2010\u2011](?=\\s)")
QUOTES = re.compile("[«»\"“”]")
UPPER = re.compile(r"\b[A-ZÀ-ÖØ-Þ]{4,}\b")
SENTENCE = re.compile(r"(?<=[.!?…])\s+")
EXCERPT = 60

FAMILIES = {
    "fr": {
        "ia-mots-creux": r"\b(revolutionnaires?|incroyables?|fascinant(?:e|es|s)?|veritables?|cruci(?:al|ale|ales|aux)|"
                         r"essentiel(?:le|les|s)?|au coeur de|un monde ou|une nouvelle ere|changer la donne)\b",
        "ia-annonce": r"\b(plongeons(?: nous)?|voyons ensemble|dans cette video|tu vas voir que|decouvrons)\b",
        "ia-fausse-confidence": r"\b(honnetement|soyons clairs?|spoiler|le truc c est que)\b",
        "ia-conclusion-vague": r"\b(l avenir nous le dira|une chose est sure|a mediter|reste a voir)\b",
    },
    "en": {
        "ia-mots-creux": r"\b(groundbreaking|revolutionary|incredible|fascinating|crucial|essential|at the heart of|"
                         r"a world where|a new era|game changer|game changing|delve)\b",
        "ia-annonce": r"\b(let s dive|let us dive|let s explore|in this video|you will see that|let s see together)\b",
        "ia-fausse-confidence": r"\b(honestly|let s be clear|spoiler|here s the thing)\b",
        "ia-conclusion-vague": r"\b(only time will tell|one thing is certain|one thing is sure|food for thought)\b",
    },
}
BINARY = {
    "fr": r"\bce n est pas\b.{0,80}?\bc est\b|\bnon seulement\b.{0,100}?\bmais\b",
    "en": r"\bit s not\b.{0,80}?\bit s\b|\bnot only\b.{0,100}?\bbut\b",
}
MESSAGES = {
    "ia-tiret": ("tiret long ou trait isolé", "Remplace-le par un point, une virgule ou deux-points"),
    "ia-mots-creux": ("mot creux", "Dis le fait précis à la place"),
    "ia-annonce": ("annonce de ce qui va être dit", "Dis-le directement, sans l'annoncer"),
    "ia-fausse-confidence": ("fausse confidence", "Retire-la et dis le fait"),
    "ia-conclusion-vague": ("conclusion vague", "Finis sur la réponse concrète"),
    "ia-majuscules": ("mot en majuscules", "Écris-le en minuscules, sauf un sigle courant"),
    "ia-guillemets": ("guillemets dans le texte dit", "Retire-les : ils sont réservés à la scène « quote »"),
}


def _excerpt(text: str, start: int, end: int) -> str:
    left = max(0, start - (EXCERPT - (end - start)) // 2)
    return text[left:left + EXCERPT].strip()


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def texts_of(part: dict, n: int) -> list[tuple[str, str, str]]:
    out = []
    if isinstance(part.get("hook"), str):
        out.append((f"Partie {n}, accroche", "say", part["hook"]))
    if isinstance(part.get("title"), str):
        out.append((f"Partie {n}, titre", "screen", part["title"]))
    for i, scene in enumerate(part.get("scenes", []), 1):
        if not isinstance(scene, dict):
            continue
        where = f"Partie {n}, scène {i}"
        say = scene.get("say")
        if isinstance(say, str):
            out.append((where, "quote-say" if scene.get("type") == "quote" else "say", say))
        props = scene.get("props")
        if isinstance(props, dict):
            for key, value in props.items():
                if scene.get("type") == "quote" and key in ("text", "speaker"):
                    continue
                out.extend((where, "screen", s) for s in _strings(value))
    return out


def _first(pattern: str, plain: str):
    return re.search(pattern, plain)


def _plain_hit(text: str, pattern: str):
    plain = countries.plain(text)
    match = _first(pattern, plain)
    return (plain, match) if match else None


def _sentences(items: list) -> list[tuple[str, str]]:
    out = []
    for where, kind, text in items:
        if kind in ("say", "quote-say"):
            out.extend((where, s) for s in SENTENCE.split(text.strip()) if s.strip())
    return out


def _word_count(sentence: str) -> int:
    return len([w for w in sentence.split() if re.search(r"\w", w)])


def findings(part: dict, n: int, lang: str) -> list[tuple[str, str, str, str]]:
    items = texts_of(part, n)
    out: list[tuple[str, str, str, str]] = []
    done: set = set()

    def add(code: str, where: str, detail: str) -> None:
        if code not in done:
            done.add(code)
            label, todo = MESSAGES[code]
            out.append((code, where, f"{label} {detail}", todo))

    for where, kind, text in items:
        match = DASH.search(text)
        if match:
            add("ia-tiret", where, f"dans « {_excerpt(text, match.start(), match.end())} »")
        if kind == "say":
            for found in UPPER.finditer(text):
                word = found.group(0)
                if word not in KNOWN_ACRONYMS and not ROMAN.match(word):
                    add("ia-majuscules", where, f"« {word} »")
                    break
            match = QUOTES.search(text)
            if match:
                add("ia-guillemets", where, f"dans « {_excerpt(text, match.start(), match.end())} »")
    for code, pattern in FAMILIES.get(lang, {}).items():
        for where, kind, text in items:
            if kind == "quote-say" and code != "ia-mots-creux":
                continue
            hit = _plain_hit(text, pattern)
            if hit:
                add(code, where, f"« {hit[1].group(0)} »")
                break
    binary = BINARY.get(lang)
    if binary:
        hits = [(where, text) for where, kind, text in items if kind != "quote-say"
                for _ in re.finditer(binary, countries.plain(text))]
        if len(hits) >= 2:
            out.append(("ia-formule-binaire", hits[0][0],
                        f"formule « ce n'est pas X, c'est Y » ou « non seulement X, mais » employée {len(hits)} fois",
                        "Garde-la une seule fois par vidéo"))
    sentences = _sentences(items)
    for i in range(len(sentences) - 2):
        run = sentences[i:i + 3]
        if all(_word_count(s) <= 3 for _, s in run):
            quoted = " ".join(s for _, s in run)
            out.append(("ia-phrases-courtes", run[0][0], f"trois phrases de trois mots ou moins de suite (« {quoted} »)",
                        "Regroupe-les, ou garde une seule phrase courte pour appuyer"))
            break
    return out
