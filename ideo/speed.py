RATES = {"fr": 3.0, "en": 3.2}
DEFAULT = 3.0


def rate(lang: str) -> float:
    return RATES.get(lang, DEFAULT)
