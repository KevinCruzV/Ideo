import json

import pytest

from ideo import plan_check

EM = chr(0x2014)


def load(job):
    return json.loads((job / "plan.json").read_text(encoding="utf-8"))


def write(job, plan):
    (job / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")


def test_valid_plan_has_no_errors(job_with_fixtures):
    assert plan_check.check_plan(job_with_fixtures) == []
    assert (job_with_fixtures / "plan.md").exists()


def test_plan_md_lists_scenes_and_source_clips(job_with_fixtures):
    plan_check.check_plan(job_with_fixtures)
    md = (job_with_fixtures / "plan.md").read_text(encoding="utf-8")
    assert "L'oubli" in md
    assert "- [shape-diagram] Le lundi tout est clair" in md
    assert "0:26" in md and "1:10" in md


def test_invalid_plan_writes_no_plan_md(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["lang"] = "de"
    write(job_with_fixtures, plan)
    plan_check.check_plan(job_with_fixtures)
    assert not (job_with_fixtures / "plan.md").exists()


@pytest.mark.parametrize("mutate,fragment", [
    (lambda p: p["parts"][0]["scenes"][1]["items"].append({"el": "x", "on": "absent"}), "« absent » n'est pas dans le texte"),
    (lambda p: p["parts"].extend([dict(p["parts"][0], n=i) for i in range(2, 10)]), "8 parties au maximum"),
    (lambda p: p["parts"][0].update(hook="Pourquoi " + EM + " vraiment ?"), "tiret cadratin"),
    (lambda p: p["parts"][0]["scenes"][0].update(type="carousel"), "type inconnu"),
    (lambda p: p.update(lang="de"), "langue"),
    (lambda p: p.update(version=2), "version"),
    (lambda p: p["parts"][0].update(n=3), "numéro"),
    (lambda p: p["parts"][0].update(hook=" "), "accroche"),
    (lambda p: p["parts"][0]["scenes"][1].update(src="99:00"), "durée de la vidéo"),
    (lambda p: p["parts"][0]["scenes"][1].update(src="abc"), "minutage invalide"),
    (lambda p: p["parts"][0]["scenes"][2].update(sfx="5:55"), "sfx.json"),
    (lambda p: p["parts"][0]["scenes"][0]["props"].update(title="a " + EM + " b"), "tiret cadratin"),
    (lambda p: p["parts"][0]["scenes"][0].pop("say"), "say"),
    (lambda p: p.update(parts=[]), "au moins 1 partie"),
    (lambda p: p.update(parts="x"), "liste"),
    (lambda p: p["parts"][0].update(scenes=[]), "scène"),
])
def test_plan_errors(job_with_fixtures, mutate, fragment):
    plan = load(job_with_fixtures)
    mutate(plan)
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any(fragment in e for e in errors), errors


def test_errors_start_with_a_location(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][0]["type"] = "carousel"
    plan["lang"] = "de"
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert len(errors) >= 2
    assert any(e.startswith("Partie 1, scène 1 : ") for e in errors)
    assert any(e.startswith("Plan : ") for e in errors)


def test_quote_not_found_points_to_closest_passage(job_with_fixtures):
    plan = load(job_with_fixtures)
    quote = plan["parts"][0]["scenes"][4]
    quote["props"]["text"] = "Nous oublions la plupart de ce que nous retenons en moins d'une semaine"
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    hit = [e for e in errors if "citation" in e]
    assert hit and hit[0].startswith("Partie 1, scène 5 : ")
    assert "[0:26]" in hit[0]


def test_quote_far_from_src_is_not_found(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][4]["src"] = "1:59"
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("citation" in e and "[0:26]" in e for e in errors), errors


@pytest.mark.parametrize("index", [0, 1, 2, 4])
def test_src_is_required_on_every_scene(job_with_fixtures, index):
    plan = load(job_with_fixtures)
    del plan["parts"][0]["scenes"][index]["src"]
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any(e.startswith(f"Partie 1, sc\u00e8ne {index + 1} : ") and "src" in e and "mm:ss" in e for e in errors), errors


def expected_estimate(job, says):
    plan = load(job)
    words = json.loads((job / "words.json").read_text(encoding="utf-8"))
    quote = plan["parts"][0]["scenes"][4]["props"]["text"].split()
    first = next(i for i, w in enumerate(words) if w["w"] == "Nous" and words[i + 1]["w"] == "oublions")
    clip = words[first + len(quote) - 1]["e"] - words[first]["s"]
    hook = len(plan["parts"][0]["hook"].split())
    return round((hook + sum(len(s.split()) for s in says)) / 2.6 + clip + 2.5 + 3.0)


def test_part_too_short_reports_estimate(job_with_fixtures):
    plan = load(job_with_fixtures)
    says = ["Court lundi jeudi."] * 5
    for scene, say in zip(plan["parts"][0]["scenes"], says):
        scene["say"] = say
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    short = [e for e in errors if "trop courte" in e]
    n = expected_estimate(job_with_fixtures, says)
    assert short and short[0].startswith("Partie 1 : ")
    assert f"dur\u00e9e estim\u00e9e {n} s" in short[0]
    assert f"Ajoute environ {45 - n} s" in short[0]


def test_part_too_long_reports_estimate(job_with_fixtures):
    plan = load(job_with_fixtures)
    scenes = plan["parts"][0]["scenes"]
    says = [s["say"] for s in scenes]
    says[0] = "mot " * 700
    scenes[0]["say"] = says[0]
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    long = [e for e in errors if "trop longue" in e]
    n = expected_estimate(job_with_fixtures, says)
    assert long and f"dur\u00e9e estim\u00e9e {n} s" in long[0]
    assert f"Coupe environ {n - 300} s" in long[0]


def test_duration_is_reported_in_the_same_pass_as_other_errors(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][0]["type"] = "carousel"
    for scene in plan["parts"][0]["scenes"]:
        scene["say"] = "Court lundi jeudi."
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("type inconnu" in e for e in errors)
    assert any("trop courte" in e for e in errors)


def test_duration_notes_unresolved_clips(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][4]["props"]["text"] = "phrase inventee sans rapport"
    for scene in plan["parts"][0]["scenes"]:
        scene["say"] = "Court lundi jeudi."
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    short = [e for e in errors if "trop courte" in e]
    assert short and "sans la dur\u00e9e de 1 extrait(s) source" in short[0]
    assert any("citation introuvable" in e for e in errors)


def test_em_dash_in_say_is_rejected(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][0]["say"] += " Et alors " + EM + " voil\u00e0."
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any(e.startswith("Partie 1, sc\u00e8ne 1 : ") and "tiret cadratin" in e for e in errors), errors


def test_hyphenated_item_matches_say(job_with_fixtures):
    plan = load(job_with_fixtures)
    scene = plan["parts"][0]["scenes"][1]
    scene["say"] += " Dis-moi si tu vois."
    scene["items"].append({"el": "labels.1", "on": "moi"})
    write(job_with_fixtures, plan)
    assert plan_check.check_plan(job_with_fixtures) == []


def test_plan_md_shows_real_clip_start_not_src(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][4]["src"] = "0:40"
    write(job_with_fixtures, plan)
    assert plan_check.check_plan(job_with_fixtures) == []
    md = (job_with_fixtures / "plan.md").read_text(encoding="utf-8")
    assert "citation \u00e0 0:26" in md and "0:40" not in md


def test_stale_plan_md_is_removed_when_check_fails(job_with_fixtures):
    assert plan_check.check_plan(job_with_fixtures) == []
    assert (job_with_fixtures / "plan.md").exists()
    plan = load(job_with_fixtures)
    plan["lang"] = "de"
    write(job_with_fixtures, plan)
    assert plan_check.check_plan(job_with_fixtures)
    assert not (job_with_fixtures / "plan.md").exists()


def test_unreadable_plan_json_is_an_error(job_with_fixtures):
    (job_with_fixtures / "plan.json").write_bytes(b"\xff\xfe\x00")
    errors = plan_check.check_plan(job_with_fixtures)
    assert errors and errors[0].startswith("Plan : ")
    (job_with_fixtures / "plan.json").unlink()
    (job_with_fixtures / "plan.json").mkdir()
    errors = plan_check.check_plan(job_with_fixtures)
    assert errors and errors[0].startswith("Plan : ") and "illisible" in errors[0]


def test_estimate_seconds():
    assert plan_check.estimate_seconds("un deux trois quatre cinq", "fr") == pytest.approx(5 / 2.6)
    assert plan_check.estimate_seconds("un deux trois quatre cinq", "en") == pytest.approx(5 / 2.8)
    assert plan_check.estimate_seconds("un deux", "es") == pytest.approx(2 / 2.6)


def test_missing_plan_json_is_an_error_not_a_traceback(job_with_fixtures):
    (job_with_fixtures / "plan.json").unlink()
    errors = plan_check.check_plan(job_with_fixtures)
    assert errors and errors[0].startswith("Plan : ") and "plan.json" in errors[0]


def test_invalid_json_is_an_error(job_with_fixtures):
    (job_with_fixtures / "plan.json").write_text("{pas du json", encoding="utf-8")
    errors = plan_check.check_plan(job_with_fixtures)
    assert errors and "JSON" in errors[0]


def test_wrong_types_never_raise(job_with_fixtures):
    for bad in ([], 3, {"version": 1, "lang": "fr", "parts": [5]},
                {"version": 1, "lang": "fr", "parts": [{"n": 1, "hook": "x", "scenes": [7, {"type": 3, "say": None, "props": [], "items": "z"}]}]}):
        write(job_with_fixtures, bad)
        errors = plan_check.check_plan(job_with_fixtures)
        assert errors and all(isinstance(e, str) for e in errors)


def test_several_parts_that_fit_one_video_are_rejected(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"].append(dict(plan["parts"][0], n=2))
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    merge = [e for e in errors if "tient en une seule vid\u00e9o" in e]
    assert merge and merge[0].startswith("Plan : ")
    assert "Fusionne les parties en une seule." in merge[0]
    total = 2 * (expected_estimate(job_with_fixtures, [s["say"] for s in plan["parts"][0]["scenes"]]))
    assert f"dur\u00e9e estim\u00e9e totale {total} s" in merge[0]
    assert not (job_with_fixtures / "plan.md").exists()


def test_several_long_parts_are_valid(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"] = [dict(plan["parts"][0], n=i) for i in range(1, 7)]
    write(job_with_fixtures, plan)
    assert plan_check.check_plan(job_with_fixtures) == []


def test_single_part_is_never_a_merge_error(job_with_fixtures):
    assert not any("tient en une seule" in e for e in plan_check.check_plan(job_with_fixtures))


@pytest.mark.parametrize("speaker", ["Chaîne Test", "chaine  test", "Mémoire et oubli !", "Ici Chaîne Test"])
def test_quote_speaker_cannot_be_the_channel_or_title(job_with_fixtures, speaker):
    (job_with_fixtures / "info.json").write_text(json.dumps(
        {"duration": 120, "channel": "Chaîne Test", "title": "Mémoire et oubli"}), encoding="utf-8")
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][4]["props"]["speaker"] = speaker
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert errors == ["Partie 1, scène 5 : « speaker » doit nommer la personne ou le média qu'on entend, pas la "
                      "chaîne YouTube. Laisse-le vide si la transcription ne le dit pas."]


def test_empty_speaker_is_valid_and_flagged_in_plan_md(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][4]["props"]["speaker"] = ""
    write(job_with_fixtures, plan)
    assert plan_check.check_plan(job_with_fixtures) == []
    md = (job_with_fixtures / "plan.md").read_text(encoding="utf-8")
    assert "voix non identifiée" in md


def test_plan_md_shows_quote_speaker(job_with_fixtures):
    assert plan_check.check_plan(job_with_fixtures) == []
    md = (job_with_fixtures / "plan.md").read_text(encoding="utf-8")
    assert "citation à 0:26 (Ebbinghaus) :" in md


def set_info(job, **info):
    (job / "info.json").write_text(json.dumps({"duration": 120, **info}), encoding="utf-8")


@pytest.mark.parametrize("mutate,where,field", [
    (lambda p: p.update(series_title="Le meilleur de Chaîne Test"), "Plan", "series_title"),
    (lambda p: p["parts"][0].update(title="Chaîne Test explique"), "Partie 1", "title"),
    (lambda p: p["parts"][0].update(hook="Dis-moi pourquoi Chaîne Test oublie tout ?"), "Partie 1", "hook"),
    (lambda p: p["parts"][0]["scenes"][0].update(say=p["parts"][0]["scenes"][0]["say"] + " Merci chaine test."), "Partie 1, scène 1", "say"),
    (lambda p: p["parts"][0]["scenes"][2]["props"]["chips"].append("CHAÎNE-TEST"), "Partie 1, scène 3", "props.chips"),
])
def test_channel_blocked_in_every_string(job_with_fixtures, mutate, where, field):
    set_info(job_with_fixtures, channel="Chaîne Test", title="Mémoire et oubli")
    plan = load(job_with_fixtures)
    mutate(plan)
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any(e.startswith(f"{where} : « {field} » contient le nom de la chaîne YouTube") and "Reformule" in e
               for e in errors), errors


def test_video_title_words_are_free_to_use(job_with_fixtures):
    set_info(job_with_fixtures, channel="Chaîne Test", title="La Lune")
    plan = load(job_with_fixtures)
    plan["series_title"] = "La Lune"
    plan["parts"][0]["title"] = "La Lune"
    plan["parts"][0]["hook"] = "Dis-moi pourquoi la lune nous fait oublier ?"
    plan["parts"][0]["scenes"][0]["say"] += " Comme la lune."
    write(job_with_fixtures, plan)
    assert plan_check.check_plan(job_with_fixtures) == []


def test_long_video_title_is_not_blocked(job_with_fixtures):
    set_info(job_with_fixtures, channel="Chaîne Test", title="Pourquoi on oublie")
    assert load(job_with_fixtures)["series_title"] == "Pourquoi on oublie"
    assert plan_check.check_plan(job_with_fixtures) == []


def test_channel_inside_quote_text_is_refused(job_with_fixtures):
    set_info(job_with_fixtures, channel="moins d'une journée")
    errors = plan_check.check_plan(job_with_fixtures)
    hits = [e for e in errors if "« props.text » contient le nom de la chaîne YouTube" in e]
    assert len(hits) == 1, errors
    assert "choisis un autre extrait qui ne nomme pas la chaîne" in hits[0]


def add_words(job, word, count):
    words = json.loads((job / "words.json").read_text(encoding="utf-8"))
    words += [{"w": word, "s": 112.0 + i, "e": 112.5 + i} for i in range(count)]
    (job / "words.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")


def say_word(job, word):
    plan = load(job)
    plan["parts"][0]["scenes"][0]["say"] += f" La {word} avance."
    write(job, plan)


def test_single_word_channel_is_blocked_when_rare_in_transcript(job_with_fixtures):
    set_info(job_with_fixtures, channel="Science")
    add_words(job_with_fixtures, "science", 3)
    say_word(job_with_fixtures, "science")
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("« say » contient le nom de la chaîne YouTube (« Science »)" in e for e in errors), errors


def test_single_word_channel_is_free_when_common_in_transcript(job_with_fixtures):
    set_info(job_with_fixtures, channel="Science")
    add_words(job_with_fixtures, "Science,", 4)
    say_word(job_with_fixtures, "science")
    assert plan_check.check_plan(job_with_fixtures) == []


def test_short_single_word_channel_is_not_blocked(job_with_fixtures):
    set_info(job_with_fixtures, channel="Lunes", title="Lune")
    say_word(job_with_fixtures, "lunes")
    assert plan_check.check_plan(job_with_fixtures) == []


def set_skip(job, hidden=(), segments=()):
    (job / "skip.json").write_text(json.dumps({
        "hidden": [{"s": s, "e": e, "probable": False} for s, e in hidden],
        "segments": [{"s": s, "e": e, "kind": "sponsor"} for s, e in segments],
    }), encoding="utf-8")


def test_src_in_hidden_sponsor_passage_is_an_error(job_with_fixtures):
    set_skip(job_with_fixtures, hidden=[(14.0, 20.0)])
    errors = plan_check.check_plan(job_with_fixtures)
    assert errors == ["Partie 1, scène 2 : « src » 0:15 est dans un passage sponsorisé (0:14 à 0:20), choisis un autre passage."]


def test_src_of_paragraph_right_after_hidden_passage_is_valid(job_with_fixtures):
    set_skip(job_with_fixtures, hidden=[(10.0, 15.4)])
    assert plan_check.check_plan(job_with_fixtures) == []


def test_sfx_and_quote_in_sponsor_segment_are_errors(job_with_fixtures):
    set_skip(job_with_fixtures, segments=[(69.0, 71.0), (20.0, 40.0)])
    errors = plan_check.check_plan(job_with_fixtures)
    assert any(e.startswith("Partie 1, scène 3 : le son 1:10 est dans un passage sponsorisé") for e in errors)
    assert any(e.startswith("Partie 1, scène 5 : la citation est dans un passage sponsorisé") for e in errors)
    assert not any("« src »" in e for e in errors)


def test_sponsor_segments_from_info_when_no_skip_json(job_with_fixtures):
    set_info(job_with_fixtures, skip=[{"s": 69.0, "e": 71.0, "kind": "sponsor"}])
    assert any("le son 1:10" in e and "sponsorisé" in e for e in plan_check.check_plan(job_with_fixtures))


def test_items_out_of_spoken_order_name_the_two_items(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][1]["items"].reverse()
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert errors == ["Partie 1, scène 2 : l'item « values.0 » (« lundi ») est dit avant l'item « values.3 » (« jeudi »). "
                      "Échange ces deux items : les items suivent l'ordre des mots dans « say ». "
                      "Ordre attendu : values.0, values.3."]


def test_items_on_the_same_word_keep_their_order(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][1]["items"] = [
        {"el": "values.0", "on": "lundi"}, {"el": "labels.0", "on": "lundi"},
        {"el": "values.3", "on": "jeudi"}, {"el": "labels.3", "on": "jeudi"},
    ]
    write(job_with_fixtures, plan)
    assert plan_check.check_plan(job_with_fixtures) == []


def test_quote_longer_than_eight_seconds_is_an_error(job_with_fixtures):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][4]["props"]["text"] = (
        "Les résultats montraient une chute très rapide dès les premières heures. "
        "Nous oublions la plupart de ce que nous apprenons en moins d'une journée")
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert len(errors) == 1
    assert errors[0].startswith("Partie 1, scène 5 : la citation dure ")
    assert errors[0].endswith(" s, 8 s au plus. Choisis une suite de mots plus courte dans le même passage.")


def test_language_without_voice_is_refused_by_check(job_with_fixtures):
    (job_with_fixtures / "lang.txt").write_text("sw", encoding="utf-8")
    plan = json.loads((job_with_fixtures / "plan.json").read_text(encoding="utf-8"))
    plan["lang"] = "sw"
    (job_with_fixtures / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("« sw »" in e and "Langues possibles" in e for e in errors)


def test_japanese_plan_without_spaces_is_measured_and_anchored(job_with_fixtures):
    (job_with_fixtures / "lang.txt").write_text("ja", encoding="utf-8")
    say = "空が青く見えるのは、太陽の光が空気の粒にぶつかって散らばるからです。青い光ほど強く散らばります。"
    scenes = [
        {"type": t, "say": say, "props": p, "items": [{"el": el, "on": "青く"}], "src": "0:10"}
        for t, p, el in [
            ("key-title", {"text": "空はなぜ青い"}, "text"),
            ("stamp", {"text": "光の散乱"}, "text"),
            ("key-title", {"text": "青い光"}, "text"),
            ("stamp", {"text": "空気の粒"}, "text"),
            ("mascot", {"bubble": "どうして？"}, "bubble"),
            ("stamp", {"text": "太陽の光"}, "text"),
            ("key-title", {"text": "散らばる光"}, "text"),
        ]
    ]
    plan = {"version": 1, "lang": "ja", "series_title": "空", "parts": [
        {"n": 1, "title": "空はなぜ青い", "hook": "空はなぜ青いのか知ってる？", "scenes": scenes}]}
    write(job_with_fixtures, plan)
    assert plan_check.check_plan(job_with_fixtures) == []
    assert plan_check.estimate_seconds(say, "ja") == pytest.approx(
        sum(1 for c in say if c.isalnum()) / plan_check.CHAR_RATES["ja"])


@pytest.mark.parametrize("field,cap", [("hook", 60), ("title", 40)])
def test_hook_and_title_caps(job_with_fixtures, field, cap):
    plan = load(job_with_fixtures)
    plan["parts"][0][field] = "Dis-moi pourquoi " + "x" * (cap + 1 - 17)
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    hits = [e for e in errors if e.startswith(f"Partie 1 : « {field} » fait ")]
    assert len(hits) == 1, errors
    assert f"caractères, {cap} au plus" in hits[0] and "raccourcis" in hits[0]


@pytest.mark.parametrize("value", ["nan", "inf", "-0:10"])
def test_non_finite_or_negative_src_is_a_plan_error(job_with_fixtures, value):
    plan = load(job_with_fixtures)
    plan["parts"][0]["scenes"][1]["src"] = value
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("minutage invalide" in e and value in e for e in errors), errors


def test_sfx_on_a_quote_scene_is_refused(job_with_fixtures):
    plan = load(job_with_fixtures)
    quote = next(s for s in plan["parts"][0]["scenes"] if s["type"] == "quote")
    quote["sfx"] = "1:10"
    write(job_with_fixtures, plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("« sfx »" in e and "quote" in e and "Retire" in e for e in errors), errors
