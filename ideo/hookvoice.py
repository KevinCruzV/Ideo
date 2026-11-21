import re

TELL_ME = {
    "fr": "Dis-moi", "en": "Tell me", "es": "Dime", "de": "Sag mir", "it": "Dimmi", "nl": "Vertel me",
    "pl": "Powiedz mi", "tr": "Söyle bana",
}
ENDING = re.compile(r"(?P<gap>\s*)(?P<marks>[.?!]+)$")


def _tell_me(lang: str) -> re.Pattern | None:
    opener = TELL_ME.get(lang)
    if not opener:
        return None
    body = r"\s+".join(re.escape(p) for p in opener.split())
    return re.compile(rf"^(?P<open>{body})(?![\w])[ ,.…]*(?P<rest>.+)$", re.IGNORECASE | re.DOTALL)


def _closing(text: str) -> str:
    stripped = text.rstrip()
    match = ENDING.search(stripped)
    if not match:
        return text
    mark = "?!" if "?" in match.group("marks") else "!"
    return stripped[:match.start()] + match.group("gap") + mark + text[len(stripped):]


def shape(text: str, lang: str) -> str:
    pattern = _tell_me(lang)
    match = pattern.match(text.strip()) if pattern else None
    if match and re.search(r"\w", match.group("rest")):
        rest = match.group("rest").strip()
        return f"{match.group('open')} ?! {_closing(rest[:1].upper() + rest[1:])}"
    return _closing(text)
