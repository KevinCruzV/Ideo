STRINGS = {
    "fr": {
        "part_label": "Partie",
        "outro_next": "Si ça t'a plu, abonne-toi pour la partie {n} : {title} !",
        "outro_last": "Si ça t'a plu, abonne-toi pour la prochaine série !",
        "outro_single": "Si ça t'a plu, abonne-toi pour la prochaine !",
        "voices_line": "Voix citées : {names}",
    },
    "en": {
        "part_label": "Part",
        "outro_next": "If you liked it, follow for part {n}: {title}!",
        "outro_last": "If you liked it, follow for the next series!",
        "outro_single": "If you liked it, follow for the next one!",
        "voices_line": "Quoted voices: {names}",
    },
    "es": {
        "part_label": "Parte",
        "outro_next": "¡Si te ha gustado, suscríbete para la parte {n}: {title}!",
        "outro_last": "¡Si te ha gustado, suscríbete para la próxima serie!",
        "outro_single": "¡Si te ha gustado, suscríbete para el próximo vídeo!",
        "voices_line": "Voces citadas: {names}",
    },
    "de": {
        "part_label": "Teil",
        "outro_next": "Wenn es dir gefallen hat, abonniere für Teil {n}: {title}!",
        "outro_last": "Wenn es dir gefallen hat, abonniere für die nächste Serie!",
        "outro_single": "Wenn es dir gefallen hat, abonniere für das nächste Video!",
        "voices_line": "Zitierte Stimmen: {names}",
    },
    "it": {
        "part_label": "Parte",
        "outro_next": "Se ti è piaciuto, iscriviti per la parte {n}: {title}!",
        "outro_last": "Se ti è piaciuto, iscriviti per la prossima serie!",
        "outro_single": "Se ti è piaciuto, iscriviti per il prossimo video!",
        "voices_line": "Voci citate: {names}",
    },
    "pt": {
        "part_label": "Parte",
        "outro_next": "Se você gostou, inscreva-se para a parte {n}: {title}!",
        "outro_last": "Se você gostou, inscreva-se para a próxima série!",
        "outro_single": "Se você gostou, inscreva-se para o próximo vídeo!",
        "voices_line": "Vozes citadas: {names}",
    },
    "nl": {
        "part_label": "Deel",
        "outro_next": "Vond je het leuk? Volg voor deel {n}: {title}!",
        "outro_last": "Vond je het leuk? Volg voor de volgende serie!",
        "outro_single": "Vond je het leuk? Volg voor de volgende video!",
        "voices_line": "Geciteerde stemmen: {names}",
    },
    "pl": {
        "part_label": "Część",
        "outro_next": "Jeśli ci się podobało, obserwuj, żeby zobaczyć część {n}: {title}!",
        "outro_last": "Jeśli ci się podobało, obserwuj, żeby zobaczyć następną serię!",
        "outro_single": "Jeśli ci się podobało, obserwuj, żeby zobaczyć następny film!",
        "voices_line": "Cytowane głosy: {names}",
    },
    "tr": {
        "part_label": "Bölüm",
        "outro_next": "Beğendiysen, {n}. bölüm için takip et: {title}!",
        "outro_last": "Beğendiysen, sonraki seri için takip et!",
        "outro_single": "Beğendiysen, sonraki video için takip et!",
        "voices_line": "Alıntılanan sesler: {names}",
    },
}


def t(key: str, lang: str, **kw) -> str:
    table = STRINGS.get(lang, {})
    return table.get(key, STRINGS["en"][key]).format(**kw)
