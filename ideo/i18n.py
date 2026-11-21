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
    "ru": {
        "part_label": "Часть",
        "outro_next": "Подпишись, чтобы увидеть часть {n}: {title}",
        "outro_last": "Подпишись, чтобы увидеть следующую серию",
        "outro_single": "Подпишись, чтобы увидеть следующее видео",
        "voices_line": "Цитируемые голоса: {names}",
    },
    "ar": {
        "part_label": "الجزء",
        "outro_next": "تابعنا لمشاهدة الجزء {n}: {title}",
        "outro_last": "تابعنا لمشاهدة السلسلة القادمة",
        "outro_single": "تابعنا لمشاهدة الفيديو القادم",
        "voices_line": "الأصوات المقتبسة: {names}",
    },
    "ja": {
        "part_label": "パート",
        "outro_next": "フォローしてパート{n}も見てね：{title}",
        "outro_last": "フォローして次のシリーズも見てね",
        "outro_single": "フォローして次の動画も見てね",
        "voices_line": "引用した声：{names}",
    },
    "ko": {
        "part_label": "파트",
        "outro_next": "팔로우하고 파트 {n}도 보세요: {title}",
        "outro_last": "팔로우하고 다음 시리즈도 보세요",
        "outro_single": "팔로우하고 다음 영상도 보세요",
        "voices_line": "인용된 목소리: {names}",
    },
    "zh": {
        "part_label": "部分",
        "outro_next": "关注我，继续看第{n}部分：{title}",
        "outro_last": "关注我，继续看下一个系列",
        "outro_single": "关注我，继续看下一个视频",
        "voices_line": "引用的声音：{names}",
    },
    "hi": {
        "part_label": "भाग",
        "outro_next": "भाग {n} के लिए फ़ॉलो करें: {title}",
        "outro_last": "अगली सीरीज़ के लिए फ़ॉलो करें",
        "outro_single": "अगले वीडियो के लिए फ़ॉलो करें",
        "voices_line": "उद्धृत आवाज़ें: {names}",
    },
}


def t(key: str, lang: str, **kw) -> str:
    table = STRINGS.get(lang, {})
    return table.get(key, STRINGS["en"][key]).format(**kw)
