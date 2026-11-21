STRINGS = {
    "fr": {
        "part_label": "Partie",
        "outro_next": "Abonne-toi pour la partie {n} : {title}",
        "outro_last": "Abonne-toi pour la prochaine série",
    },
    "en": {
        "part_label": "Part",
        "outro_next": "Follow for part {n}: {title}",
        "outro_last": "Follow for the next series",
    },
    "es": {
        "part_label": "Parte",
        "outro_next": "Suscríbete para la parte {n}: {title}",
        "outro_last": "Suscríbete para la próxima serie",
    },
    "de": {
        "part_label": "Teil",
        "outro_next": "Abonniere für Teil {n}: {title}",
        "outro_last": "Abonniere für die nächste Serie",
    },
    "it": {
        "part_label": "Parte",
        "outro_next": "Iscriviti per la parte {n}: {title}",
        "outro_last": "Iscriviti per la prossima serie",
    },
    "pt": {
        "part_label": "Parte",
        "outro_next": "Inscreva-se para a parte {n}: {title}",
        "outro_last": "Inscreva-se para a próxima série",
    },
}


def t(key: str, lang: str, **kw) -> str:
    table = STRINGS.get(lang, STRINGS["en"])
    return table[key].format(**kw)
