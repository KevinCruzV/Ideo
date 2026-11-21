STRINGS = {
    "fr": {
        "part_label": "Partie",
        "outro_next": "Abonne-toi pour la partie {n} : {title}",
        "outro_last": "Abonne-toi pour la prochaine série",
        "outro_single": "Abonne-toi pour la prochaine vidéo",
    },
    "en": {
        "part_label": "Part",
        "outro_next": "Follow for part {n}: {title}",
        "outro_last": "Follow for the next series",
        "outro_single": "Follow for the next video",
    },
    "es": {
        "part_label": "Parte",
        "outro_next": "Suscríbete para la parte {n}: {title}",
        "outro_last": "Suscríbete para la próxima serie",
        "outro_single": "Suscríbete para el próximo vídeo",
    },
    "de": {
        "part_label": "Teil",
        "outro_next": "Abonniere für Teil {n}: {title}",
        "outro_last": "Abonniere für die nächste Serie",
        "outro_single": "Abonniere für das nächste Video",
    },
    "it": {
        "part_label": "Parte",
        "outro_next": "Iscriviti per la parte {n}: {title}",
        "outro_last": "Iscriviti per la prossima serie",
        "outro_single": "Iscriviti per il prossimo video",
    },
    "pt": {
        "part_label": "Parte",
        "outro_next": "Inscreva-se para a parte {n}: {title}",
        "outro_last": "Inscreva-se para a próxima série",
        "outro_single": "Inscreva-se para o próximo vídeo",
    },
}


def t(key: str, lang: str, **kw) -> str:
    table = STRINGS.get(lang, STRINGS["en"])
    return table[key].format(**kw)
