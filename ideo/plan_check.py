from pathlib import Path

from ideo import scene_schema, speed, voice
from ideo.common import fmt_ts, load_json, parse_ts
from ideo.textmatch import SPLIT, anchor_text, closest_passage, find_span, normalize

SCENE_TYPES = frozenset({
    "key-title", "person-card", "fact-chips", "stack-list", "counter", "timeline",
    "icon-grid", "stamp", "quote", "object-state", "shape-diagram", "mascot", "versus", "map", "body",
})
MAX_PARTS = 8
MAX_SCENES = 45
MIN_SECONDS = 45
MAX_SECONDS = 300
OUTRO_SECONDS = 3.0
QUOTE_WINDOW = 90.0
QUOTE_MAX_SECONDS = 8.0
EM_DASH = chr(0x2014)
CHANNEL_MIN_CHARS = 6
CHANNEL_MAX_SPOKEN = 3
RATES = {"fr": 2.6, "en": 2.8}
TRIM = 0.06
GAP_HOOK = 0.60 + TRIM
GAP_SCENE = 0.50 + TRIM
GAP_BREAK = 0.90 + TRIM


def pause_seconds(scenes: list) -> float:
    def broken(scene) -> bool:
        return isinstance(scene, dict) and scene.get("break") is True

    total = GAP_BREAK if broken(scenes[0]) else GAP_HOOK
    total += sum(GAP_BREAK if broken(s) else GAP_SCENE for s in scenes[1:])
    return total + GAP_SCENE


def estimate_seconds(text: str, lang: str) -> float:
    return len(text.split()) / speed.rate(lang)


def read_json(job: Path, name: str, default):
    path = job / name
    if not path.exists():
        return default
    try:
        return load_json(path)
    except (ValueError, OSError):
        return default


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _ts(value, where: str, field: str, errors: list[str]):
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where} : « {field} » doit être un minutage texte « mm:ss » ou « h:mm:ss », par exemple « 12:30 ».")
        return None
    try:
        return parse_ts(value)
    except ValueError:
        errors.append(f"{where} : minutage invalide « {value} » dans « {field} ». Écris « mm:ss » ou « h:mm:ss », par exemple « 12:30 ».")
        return None


def _text_field(obj: dict, key: str, where: str, errors: list[str]) -> str | None:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where} : « {key} » est manquant ou vide. Écris le texte de « {key} » en une chaîne non vide.")
        return None
    return value


def _check_dash(texts, where: str, errors: list[str]) -> None:
    for text in texts:
        if EM_DASH in text:
            errors.append(f"{where} : tiret cadratin interdit dans « {text[:60]} ». Remplace-le par une virgule, deux-points ou un point.")
            return


def blocked_channel(info, words: list[dict]) -> str | None:
    if not isinstance(info, dict) or not isinstance(info.get("channel"), str):
        return None
    channel = info["channel"]
    plain = _plain(channel).split()
    if len(plain) >= 2:
        return channel
    if len(plain) == 1 and len(plain[0]) >= CHANNEL_MIN_CHARS:
        spoken = sum(_plain(w["w"]).split().count(plain[0]) for w in words)
        if spoken <= CHANNEL_MAX_SPOKEN:
            return channel
    return None


def _check_channel(fields, where: str, ctx: dict, errors: list[str], quoted: tuple = ()) -> None:
    name = ctx["channel"]
    if name is None:
        return
    for field, text in fields:
        if isinstance(text, str) and find_span(text.split(), name) is not None:
            if field in quoted:
                fix = "Une citation ne se reformule pas : choisis un autre extrait qui ne nomme pas la chaîne."
            else:
                fix = "Reformule sans le reprendre : on ne nomme jamais la chaîne ni la personne qui l'anime."
            errors.append(f"{where} : « {field} » contient le nom de la chaîne YouTube (« {name} »). {fix}")
            return


def _prop_strings(kind, props: dict):
    for key, value in props.items():
        if kind == "quote" and key == "speaker":
            continue
        for text in _strings(value):
            yield f"props.{key}", text


def _ranges(value) -> list[tuple[float, float]]:
    out = []
    for r in value if isinstance(value, list) else []:
        try:
            out.append((float(r["s"]), float(r["e"])))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def sponsor_ranges(job: Path, info) -> tuple[list, list]:
    skip = read_json(job, "skip.json", {})
    skip = skip if isinstance(skip, dict) else {}
    segments = skip.get("segments") if "segments" in skip else (info.get("skip") if isinstance(info, dict) else [])
    hidden = _ranges(skip.get("hidden"))
    return hidden, hidden + _ranges(segments)


def end_ranges(job: Path) -> set:
    skip = read_json(job, "skip.json", {})
    entries = skip.get("hidden") if isinstance(skip, dict) else []
    out = set()
    for entry in entries if isinstance(entries, list) else []:
        if isinstance(entry, dict) and entry.get("end") is True:
            try:
                out.add((float(entry["s"]), float(entry["e"])))
            except (KeyError, TypeError, ValueError):
                continue
    return out


def _sponsored(start: float, end: float, ranges: list) -> tuple[float, float] | None:
    return next(((s, e) for s, e in ranges if start < e and end > s), None)


def _sponsor_error(where: str, what: str, hit: tuple[float, float], ends=()) -> str:
    span = f"{fmt_ts(hit[0])} à {fmt_ts(hit[1])}"
    if hit in ends:
        return (f"{where} : {what} est dans la fin de la vidéo (remerciements, appel à s'abonner), "
                f"ignorée ({span}), choisis un autre passage.")
    return f"{where} : {what} est dans un passage sponsorisé ({span}), choisis un autre passage."


def _sfx_by_ts(sfx: list) -> dict:
    out = {}
    for entry in sfx:
        if isinstance(entry, dict) and isinstance(entry.get("at"), str):
            try:
                out[round(parse_ts(entry["at"]), 2)] = entry
            except ValueError:
                continue
    return out


def _check_scene(scene, where: str, ctx: dict, errors: list[str], part_state: dict) -> None:
    if not isinstance(scene, dict):
        errors.append(f"{where} : la scène doit être un objet JSON avec « type », « say » et « props ».")
        part_state["usable"] = False
        return
    kind = scene.get("type")
    if not isinstance(kind, str) or kind not in SCENE_TYPES:
        errors.append(f"{where} : type inconnu « {kind} ». Types possibles : {', '.join(sorted(SCENE_TYPES))}.")
    say = _text_field(scene, "say", where, errors)
    if say is None:
        part_state["usable"] = False
    else:
        part_state["seconds"] += estimate_seconds(say, ctx["lang"])
        _check_dash([say], where, errors)
    props = scene.get("props", {})
    if not isinstance(props, dict):
        errors.append(f"{where} : « props » doit être un objet JSON.")
        props = {}
    _check_dash(_strings(props), where, errors)
    known = isinstance(kind, str) and kind in SCENE_TYPES
    if known:
        errors.extend(scene_schema.check_props(kind, props, where))
    quoted = ("props.text",) if kind == "quote" else ()
    _check_channel([("say", say)] + list(_prop_strings(kind, props)), where, ctx, errors, quoted)

    if "break" in scene and not isinstance(scene["break"], bool):
        errors.append(f"{where} : « break » doit être true ou false (nouvel acte, pause avant la scène). Retire-le ou corrige-le.")

    items = scene.get("items", [])
    if not isinstance(items, list):
        errors.append(f"{where} : « items » doit être une liste d'objets {{\"el\": ..., \"on\": ...}}.")
        items = []
    spoken = []
    for item in items:
        anchor = anchor_text(item.get("on")) if isinstance(item, dict) else None
        if anchor is None:
            errors.append(f"{where} : chaque élément de « items » doit avoir « el » et un « on » non vide (texte ou nombre) qui apparaît dans « say ».")
            continue
        if known:
            errors.extend(scene_schema.check_el(kind, props, item.get("el"), where))
        span = find_span(say.split(), anchor) if say is not None else None
        if say is not None and span is None:
            errors.append(f"{where} : « {anchor} » n'est pas dans le texte de « say ». Recopie dans « on » un mot ou une suite de mots exacts de « say », ou corrige « say ».")
        elif span is not None:
            spoken.append((span[0], item))
    _check_order(spoken, where, errors)

    src_seconds = None
    if "src" not in scene:
        errors.append(f"{where} : « src » est manquant. Recopie le « mm:ss » du paragraphe de la transcription compacte qui justifie cette scène.")
    else:
        src_seconds = _ts(scene["src"], where, "src", errors)
        if src_seconds is not None and ctx["duration"] is not None and src_seconds > ctx["duration"]:
            errors.append(f"{where} : « src » {scene['src']} dépasse la durée de la vidéo ({fmt_ts(ctx['duration'])}). Utilise le minutage d'un paragraphe de la transcription compacte.")
        if src_seconds is not None:
            hit = next(((a, b) for a, b in ctx["hidden"] if a <= src_seconds < int(b)), None)
            if hit:
                errors.append(_sponsor_error(where, f"« src » {scene['src']}", hit, ctx["ends"]))

    if "sfx" in scene and kind == "quote":
        errors.append(f"{where} : « sfx » sur une scène « quote » ne serait pas joué, la citation joue déjà la vraie voix. Retire « sfx » ou mets-le sur une autre scène.")
        part_state["unresolved"] += 1
    elif "sfx" in scene:
        at = _ts(scene["sfx"], where, "sfx", errors)
        if at is None:
            part_state["unresolved"] += 1
        else:
            entry = ctx["sfx"].get(round(at, 2))
            if entry is None:
                part_state["unresolved"] += 1
                available = ", ".join(e["at"] for e in ctx["sfx"].values()) or "aucun"
                errors.append(f"{where} : le son {scene['sfx']} n'est pas dans sfx.json. Repères disponibles : {available}. Prends l'un d'eux ou retire « sfx ».")
            else:
                try:
                    part_state["seconds"] += max(0.0, float(entry["e"]) - float(entry["s"]))
                    hit = _sponsored(float(entry["s"]), float(entry["e"]), ctx["sponsor"])
                except (KeyError, TypeError, ValueError):
                    hit = None
                if hit:
                    errors.append(_sponsor_error(where, f"le son {scene['sfx']}", hit, ctx["ends"]))
                part_state["clips"].append(("sfx", scene["sfx"], "", ""))

    if kind == "quote":
        _check_quote(scene, props, src_seconds, where, ctx, errors, part_state)


def _check_order(spoken: list, where: str, errors: list[str]) -> None:
    for (before, first), (after, second) in zip(spoken, spoken[1:]):
        if after < before:
            order = ", ".join(str(item.get("el")) for _, item in sorted(spoken, key=lambda pair: pair[0]))
            errors.append(f"{where} : l'item « {second.get('el')} » (« {anchor_text(second['on'])} ») est dit avant l'item « {first.get('el')} » (« {anchor_text(first['on'])} »). "
                          f"Échange ces deux items : les items suivent l'ordre des mots dans « say ». Ordre attendu : {order}.")
            return


def _plain(value) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(n for n in (normalize(t) for t in SPLIT.split(value)) if n)


def _check_quote(scene, props, src_seconds, where, ctx, errors, part_state) -> None:
    speaker = props.get("speaker")
    speaker = speaker.strip() if isinstance(speaker, str) else ""
    named = ctx["channel"] is not None and find_span(speaker.split(), ctx["channel"]) is not None
    if speaker and (named or _plain(speaker) in ctx["publisher"]):
        errors.append(f"{where} : « speaker » doit nommer la personne ou le média qu'on entend, pas la chaîne YouTube. Laisse-le vide si la transcription ne le dit pas.")
    text = props.get("text")
    if not isinstance(text, str) or not text.strip():
        errors.append(f"{where} : une scène « quote » demande « props.text », la citation exacte dite dans la vidéo.")
        part_state["unresolved"] += 1
        return
    if src_seconds is None:
        part_state["unresolved"] += 1
        return
    words = ctx["words"]
    window = [w for w in words if abs(w["s"] - src_seconds) <= QUOTE_WINDOW]
    span = find_span([w["w"] for w in window], text) if window else None
    if span is None:
        hint = closest_passage(words, text) if words else "transcription vide"
        errors.append(f"{where} : citation introuvable à ± 90 s de {scene['src']}. Passage le plus proche : {hint}. Recopie la citation exacte de ce passage dans « props.text », ou corrige « src ».")
        part_state["unresolved"] += 1
        return
    clip = window[span[1]]["e"] - window[span[0]]["s"]
    if clip > QUOTE_MAX_SECONDS:
        errors.append(f"{where} : la citation dure {round(clip)} s, {QUOTE_MAX_SECONDS:.0f} s au plus. Choisis une suite de mots plus courte dans le même passage.")
    hit = _sponsored(window[span[0]]["s"], window[span[1]]["e"], ctx["sponsor"])
    if hit:
        errors.append(_sponsor_error(where, "la citation", hit, ctx["ends"]))
    part_state["seconds"] += clip
    part_state["clips"].append(("citation", fmt_ts(window[span[0]]["s"]), text, speaker or "voix non identifiée"))


def _check_part(part, index: int, ctx: dict, errors: list[str]) -> tuple[list, float | None]:
    where = f"Partie {index}"
    if not isinstance(part, dict):
        errors.append(f"{where} : la partie doit être un objet JSON avec « n », « title », « hook » et « scenes ».")
        return [], None
    if part.get("n") != index:
        errors.append(f"{where} : numéro « n » = {part.get('n')!r}, attendu {index}. Numérote les parties 1, 2, 3, dans l'ordre.")
    _text_field(part, "title", where, errors)
    hook = part.get("hook")
    state = {"seconds": OUTRO_SECONDS, "clips": [], "usable": True, "unresolved": 0}
    if not isinstance(hook, str) or not hook.strip():
        errors.append(f"{where} : l'accroche « hook » est manquante ou vide. Écris une phrase d'accroche qui donne envie de regarder.")
        state["usable"] = False
    else:
        state["seconds"] += estimate_seconds(hook, ctx["lang"])
        _check_dash([hook], where, errors)
    question = part.get("question")
    if not isinstance(question, str) or not question.strip():
        errors.append(f"{where} : la « question » au spectateur est manquante. Écris une question courte et engageante sur le sujet, "
                      "posée juste avant l'appel à s'abonner, par exemple « Et toi, dans quelle position tu dors ? ».")
    else:
        state["seconds"] += estimate_seconds(question, ctx["lang"])
        _check_dash([question], where, errors)
        if not question.rstrip().endswith("?"):
            errors.append(f"{where} : la « question » doit finir par un point d'interrogation, c'est une question posée au spectateur.")
    if isinstance(part.get("title"), str):
        _check_dash([part["title"]], where, errors)
    for field in ("title", "hook", "question"):
        if isinstance(part.get(field), str):
            error = scene_schema.cap_error(where, field, part[field], scene_schema.PART_CAPS[field])
            if error:
                errors.append(error)
    _check_channel([("title", part.get("title")), ("hook", hook), ("question", question)], where, ctx, errors)
    scenes = part.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append(f"{where} : « scenes » doit être une liste d'au moins une scène.")
        return [], None
    if len(scenes) > MAX_SCENES:
        errors.append(f"{where} : {len(scenes)} scènes, {MAX_SCENES} au plus par vidéo. Retire ou fusionne {len(scenes) - MAX_SCENES} scène(s), ou découpe en plusieurs parties.")
    for k, scene in enumerate(scenes, 1):
        _check_scene(scene, f"{where}, scène {k}", ctx, errors, state)
    state["seconds"] += pause_seconds(scenes)
    if not state["usable"]:
        return state["clips"], None
    total = round(state["seconds"])
    note = ""
    if state["unresolved"]:
        note = f" (sans la durée de {state['unresolved']} extrait(s) source non résolu(s), corrige-les d'abord)"
    if total < MIN_SECONDS:
        errors.append(f"{where} : durée estimée {total} s{note}, trop courte (minimum {MIN_SECONDS} s). Ajoute environ {MIN_SECONDS - total} s de texte « say » ou une scène.")
    elif total > MAX_SECONDS:
        errors.append(f"{where} : durée estimée {total} s{note}, trop longue (maximum {MAX_SECONDS} s). Coupe environ {total - MAX_SECONDS} s de texte « say » ou une scène, ou découpe en plusieurs parties.")
    return state["clips"], state["seconds"]


def pace_line(seconds: int, scenes: int) -> str:
    rhythm = str(round(scenes / (seconds / 60), 1) if seconds else 0.0).replace(".", ",")
    return f"Durée estimée : environ {seconds} s, {scenes} scènes, {rhythm} scènes par minute."


def _write_md(job: Path, plan: dict, clips_by_part: list, stats: dict) -> None:
    lines = [f"# {plan['series_title']}" if plan.get("series_title") else "# Plan", "",
             pace_line(stats["seconds"], stats["scenes"]), ""]
    for part, clips in zip(plan["parts"], clips_by_part):
        lines += [f"## Partie {part['n']} : {part['title']}", "", f"Accroche : {part['hook']}", ""]
        lines += [f"- [{s['type']}] {s['say']}" for s in part["scenes"]]
        lines += ["", "Extraits audio source conservés :"]
        lines += [f"- {kind} à {ts}" + (f" ({who})" if who else "") + (f" : {text}" if text else "")
                  for kind, ts, text, who in clips] or ["- aucun"]
        lines.append("")
    (job / "plan.md").write_text("\n".join(lines), encoding="utf-8")


MAX_WISHES = 5
WISH_CAP = 40


def _check_wishes(plan: dict, errors: list[str]) -> None:
    if "wishes" not in plan:
        return
    wishes = plan["wishes"]
    if not isinstance(wishes, list) or len(wishes) > MAX_WISHES:
        errors.append(f"Plan : « wishes » doit être une liste de 0 à {MAX_WISHES} textes courts (les dessins qui t'ont manqué). "
                      "Retire les souhaits en trop ou supprime le champ.")
        return
    for i, wish in enumerate(wishes):
        if not isinstance(wish, str) or not wish.strip():
            errors.append(f"Plan : « wishes.{i} » doit être un texte non vide. Écris le dessin voulu en quelques mots ou retire-le.")
            continue
        _check_dash([wish], "Plan", errors)
        error = scene_schema.cap_error("Plan", f"wishes.{i}", wish, WISH_CAP)
        if error:
            errors.append(error)


def _analyze(job: Path) -> tuple[list[str], dict | None]:
    job = Path(job)
    path = job / "plan.json"
    (job / "plan.md").unlink(missing_ok=True)
    if not path.exists():
        return ["Plan : plan.json est introuvable. Écris-le dans le dossier du job avant de lancer la validation."], None
    try:
        plan = load_json(path)
    except ValueError as exc:
        return [f"Plan : plan.json n'est pas un JSON valide ({exc}). Corrige la syntaxe puis relance."], None
    except OSError as exc:
        return [f"Plan : plan.json est illisible ({exc}). Vérifie le fichier puis relance."], None
    if not isinstance(plan, dict):
        return ["Plan : plan.json doit contenir un objet JSON avec « version », « lang », « series_title » et « parts »."], None

    errors: list[str] = []
    lang_file = job / "lang.txt"
    job_lang = lang_file.read_text(encoding="utf-8").strip() if lang_file.exists() else None
    if plan.get("version") != 1:
        errors.append(f"Plan : version {plan.get('version')!r} non supportée. Mets « version »: 1.")
    lang = plan.get("lang")
    if not isinstance(lang, str) or (job_lang is not None and lang != job_lang):
        errors.append(f"Plan : langue « {lang} » différente de celle de la vidéo (« {job_lang} »). Mets « lang »: « {job_lang} » et écris tous les textes dans cette langue.")
    elif voice.unsupported(lang):
        errors.append(f"Plan : {voice.unsupported(lang)}")
    if "series_title" in plan:
        _check_dash([plan["series_title"]] if isinstance(plan["series_title"], str) else [], "Plan", errors)

    _check_wishes(plan, errors)
    parts = plan.get("parts")
    if not isinstance(parts, list):
        errors.append("Plan : « parts » doit être une liste de parties.")
        return errors, None
    if not parts:
        errors.append("Plan : il faut au moins 1 partie dans « parts ».")
    if len(parts) > MAX_PARTS:
        errors.append(f"Plan : {len(parts)} parties, {MAX_PARTS} parties au maximum. Regroupe ou retire des parties.")

    info = read_json(job, "info.json", {})
    duration = info.get("duration") if isinstance(info, dict) else None
    words = read_json(job, "words.json", [])
    if not isinstance(words, list):
        words = []
    words = [w for w in words if isinstance(w, dict) and isinstance(w.get("w"), str) and "s" in w and "e" in w]
    sfx = read_json(job, "sfx.json", [])
    hidden, sponsor = sponsor_ranges(job, info)
    publisher = {_plain(info.get(k)) for k in ("channel", "title")} if isinstance(info, dict) else set()
    ctx = {
        "publisher": publisher - {""},
        "channel": blocked_channel(info, words),
        "lang": lang if isinstance(lang, str) else (job_lang or "fr"),
        "duration": float(duration) if isinstance(duration, (int, float)) else None,
        "words": words,
        "sfx": _sfx_by_ts(sfx if isinstance(sfx, list) else []),
        "hidden": hidden,
        "ends": end_ranges(job),
        "sponsor": sponsor,
    }
    _check_channel([("series_title", plan.get("series_title"))], "Plan", ctx, errors)
    results = [_check_part(part, i, ctx, errors) for i, part in enumerate(parts, 1)]
    clips_by_part = [clips for clips, _ in results]
    seconds = [sec for _, sec in results]
    if len(parts) > 1 and all(sec is not None for sec in seconds) and sum(seconds) <= MAX_SECONDS:
        errors.append(f"Plan : le contenu tient en une seule vidéo (durée estimée totale {round(sum(seconds))} s). Fusionne les parties en une seule.")
    stats = None
    if not errors:
        total = round(sum(seconds))
        count = sum(len(part["scenes"]) for part in parts)
        stats = {"seconds": total, "scenes": count, "plan": plan, "lang": lang, "source": ctx["duration"]}
        _write_md(job, plan, clips_by_part, stats)
    return errors, stats


def check_plan(job: Path) -> list[str]:
    return analyze(job)["errors"]


def analyze(job: Path) -> dict:
    errors, stats = _analyze(job)
    return {"errors": errors, "stats": stats}
