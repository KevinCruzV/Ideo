RATES = {"fr": 3.4, "en": 3.6}
DEFAULT = 3.4


def rate(lang: str) -> float:
    return RATES.get(lang, DEFAULT)
