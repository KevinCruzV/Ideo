STRINGS = {
    "fr": {
        "part_label": "Partie",
        "outro_next": "Abonne-toi pour la partie {n} : {title}",
        "outro_last": "Abonne-toi pour la prochaine série",
        "outro_single": "Abonne-toi pour la prochaine vidéo",
        "voices_line": "Voix citées : {names}",
    },
    "en": {
        "part_label": "Part",
        "outro_next": "Follow for part {n}: {title}",
        "outro_last": "Follow for the next series",
        "outro_single": "Follow for the next video",
        "voices_line": "Quoted voices: {names}",
    },
    "es": {
        "part_label": "Parte",
        "outro_next": "Suscríbete para la parte {n}: {title}",
        "outro_last": "Suscríbete para la próxima serie",
        "outro_single": "Suscríbete para el próximo vídeo",
        "voices_line": "Voces citadas: {names}",
    },
    "de": {
        "part_label": "Teil",
        "outro_next": "Abonniere für Teil {n}: {title}",
        "outro_last": "Abonniere für die nächste Serie",
        "outro_single": "Abonniere für das nächste Video",
        "voices_line": "Zitierte Stimmen: {names}",
    },
    "it": {
        "part_label": "Parte",
        "outro_next": "Iscriviti per la parte {n}: {title}",
        "outro_last": "Iscriviti per la prossima serie",
        "outro_single": "Iscriviti per il prossimo video",
        "voices_line": "Voci citate: {names}",
    },
    "pt": {
        "part_label": "Parte",
        "outro_next": "Inscreva-se para a parte {n}: {title}",
        "outro_last": "Inscreva-se para a próxima série",
        "outro_single": "Inscreva-se para o próximo vídeo",
        "voices_line": "Vozes citadas: {names}",
    },
    "nl": {
        "part_label": "Deel",
        "outro_next": "Volg voor deel {n}: {title}",
        "outro_last": "Volg voor de volgende serie",
        "outro_single": "Volg voor de volgende video",
        "voices_line": "Geciteerde stemmen: {names}",
    },
    "pl": {
        "part_label": "Część",
        "outro_next": "Obserwuj, żeby zobaczyć część {n}: {title}",
        "outro_last": "Obserwuj, żeby zobaczyć następną serię",
        "outro_single": "Obserwuj, żeby zobaczyć następny film",
        "voices_line": "Cytowane głosy: {names}",
    },
    "tr": {
        "part_label": "Bölüm",
        "outro_next": "{n}. bölüm için takip et: {title}",
        "outro_last": "Sonraki seri için takip et",
        "outro_single": "Sonraki video için takip et",
        "voices_line": "Alıntılanan sesler: {names}",
    },
}


def t(key: str, lang: str, **kw) -> str:
    table = STRINGS.get(lang, {})
    return table.get(key, STRINGS["en"][key]).format(**kw)
