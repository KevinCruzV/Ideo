import re

from ideo import textmatch

NAMES = {
    "us": ("États-Unis", "Etats Unis", "États-Unis d'Amérique", "USA", "United States", "United States of America"),
    "cn": ("Chine", "China"),
    "ru": ("Russie", "Russia"),
    "in": ("Inde", "India"),
    "br": ("Brésil", "Brazil"),
    "za": ("Afrique du Sud", "South Africa"),
    "fr": ("France",),
    "gb": ("Royaume-Uni", "UK", "United Kingdom", "Grande-Bretagne", "Great Britain", "Britain", "Angleterre", "England"),
    "de": ("Allemagne", "Germany"),
    "it": ("Italie", "Italy"),
    "es": ("Espagne", "Spain"),
    "pt": ("Portugal",),
    "jp": ("Japon", "Japan"),
    "kr": ("Corée du Sud", "South Korea"),
    "kp": ("Corée du Nord", "North Korea"),
    "ca": ("Canada",),
    "au": ("Australie", "Australia"),
    "mx": ("Mexique", "Mexico"),
    "ar": ("Argentine", "Argentina"),
    "cl": ("Chili", "Chile"),
    "co": ("Colombie", "Colombia"),
    "pe": ("Pérou", "Peru"),
    "ve": ("Venezuela",),
    "cu": ("Cuba",),
    "tr": ("Turquie", "Turkey", "Türkiye"),
    "ir": ("Iran",),
    "iq": ("Irak", "Iraq"),
    "sa": ("Arabie saoudite", "Saudi Arabia"),
    "ae": ("Émirats arabes unis", "United Arab Emirates", "UAE"),
    "il": ("Israël", "Israel"),
    "ps": ("Palestine",),
    "eg": ("Égypte", "Egypt"),
    "dz": ("Algérie", "Algeria"),
    "ma": ("Maroc", "Morocco"),
    "tn": ("Tunisie", "Tunisia"),
    "ly": ("Libye", "Libya"),
    "ng": ("Nigeria", "Nigéria"),
    "et": ("Éthiopie", "Ethiopia"),
    "ke": ("Kenya",),
    "gh": ("Ghana",),
    "sn": ("Sénégal", "Senegal"),
    "cd": ("République démocratique du Congo", "RDC", "Democratic Republic of the Congo", "DR Congo"),
    "ao": ("Angola",),
    "zw": ("Zimbabwe",),
    "ua": ("Ukraine",),
    "pl": ("Pologne", "Poland"),
    "nl": ("Pays-Bas", "Netherlands", "The Netherlands", "Hollande"),
    "be": ("Belgique", "Belgium"),
    "ch": ("Suisse", "Switzerland"),
    "at": ("Autriche", "Austria"),
    "se": ("Suède", "Sweden"),
    "no": ("Norvège", "Norway"),
    "dk": ("Danemark", "Denmark"),
    "fi": ("Finlande", "Finland"),
    "ie": ("Irlande", "Ireland"),
    "gr": ("Grèce", "Greece"),
    "hu": ("Hongrie", "Hungary"),
    "cz": ("Tchéquie", "République tchèque", "Czech Republic", "Czechia"),
    "ro": ("Roumanie", "Romania"),
    "bg": ("Bulgarie", "Bulgaria"),
    "rs": ("Serbie", "Serbia"),
    "hr": ("Croatie", "Croatia"),
    "by": ("Biélorussie", "Belarus"),
    "kz": ("Kazakhstan",),
    "uz": ("Ouzbékistan", "Uzbekistan"),
    "af": ("Afghanistan",),
    "pk": ("Pakistan",),
    "bd": ("Bangladesh",),
    "lk": ("Sri Lanka",),
    "np": ("Népal", "Nepal"),
    "th": ("Thaïlande", "Thailand"),
    "vn": ("Vietnam", "Viêt Nam"),
    "id": ("Indonésie", "Indonesia"),
    "my": ("Malaisie", "Malaysia"),
    "sg": ("Singapour", "Singapore"),
    "ph": ("Philippines",),
    "tw": ("Taïwan", "Taiwan"),
    "mn": ("Mongolie", "Mongolia"),
    "nz": ("Nouvelle-Zélande", "New Zealand"),
    "sy": ("Syrie", "Syria"),
    "lb": ("Liban", "Lebanon"),
    "jo": ("Jordanie", "Jordan"),
    "qa": ("Qatar",),
    "kw": ("Koweït", "Kuwait"),
    "ye": ("Yémen", "Yemen"),
    "su": ("URSS", "Union soviétique", "Soviet Union", "USSR"),
    "eu": ("Union européenne", "European Union"),
    "un": ("ONU", "Nations unies", "United Nations"),
}


def plain(text: str) -> str:
    parts = [textmatch.normalize(p) for p in re.split(r"[\s\-'’]+", text)]
    return " ".join(p for p in parts if p)


LOOKUP = {plain(name): code for code, names in NAMES.items() for name in names}


DISPLAY = {code: names[0] for code, names in NAMES.items()}
KEYS = sorted(((key.split(), code) for key, code in LOOKUP.items()), key=lambda item: -len(item[0]))


def _find(tokens: list[str], start: int = 0) -> list[tuple[int, str]]:
    found, i = [], start
    while i < len(tokens):
        for words, code in KEYS:
            if tokens[i:i + len(words)] == words:
                found.append((i, code))
                i += len(words) - 1
                break
        i += 1
    return found


def mentions(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for _, code in _find(plain(text).split()):
        if code not in [c for c, _ in out]:
            out.append((code, DISPLAY[code]))
    return out


def flag_wish(text: str) -> tuple[str, str] | None:
    tokens = plain(text).split()
    for i, token in enumerate(tokens):
        if token in ("drapeau", "drapeaux"):
            hits = _find(tokens, i + 1)
            if hits:
                code = hits[0][1]
                return code, DISPLAY[code]
    return None


def code_of(label) -> str | None:
    return LOOKUP.get(plain(label)) if isinstance(label, str) else None
