import math

import pytest

from ideo import align, common, timeline


def test_anchor_found_with_normalisation():
    words = [{"w": "Il", "s": 0.0, "e": 0.2}, {"w": "verrouille,", "s": 0.3, "e": 0.8}]
    assert timeline.anchor_frame(words, "verrouille", seg_start=10.0, seg_dur=1.0, say="Il verrouille") == 309


def test_anchor_accents_and_case_are_normalised():
    words = [{"w": "La", "s": 0.0, "e": 0.2}, {"w": "Mémoire.", "s": 1.0, "e": 1.5}]
    assert timeline.anchor_frame(words, "memoire", 0.0, 2.0, "La mémoire") == 30


def test_anchor_missing_falls_back_to_proportional_position():
    words = [{"w": "En", "s": 0.0, "e": 0.2}, {"w": "mille", "s": 0.3, "e": 0.6},
             {"w": "huit", "s": 0.7, "e": 0.9}, {"w": "cent", "s": 1.0, "e": 1.2},
             {"w": "quatre-vingt-cinq", "s": 1.3, "e": 2.0}, {"w": "il", "s": 2.2, "e": 2.4},
             {"w": "commence", "s": 2.5, "e": 3.0}]
    f = timeline.anchor_frame(words, "1885", seg_start=0.0, seg_dur=4.0, say="En 1885 il commence")
    assert 15 <= f <= 45


def test_anchor_fallback_uses_seg_start_and_never_raises_on_empty_words():
    f = timeline.anchor_frame([], "1885", seg_start=2.0, seg_dur=4.0, say="En 1885 il commence")
    assert 75 <= f <= 105


def test_anchor_fallback_when_anchor_not_in_say_is_segment_start():
    assert timeline.anchor_frame([], "zzz", seg_start=1.0, seg_dur=4.0, say="rien") == 30


def test_anchor_elision_matches_inside_contraction():
    words = [{"w": "Sur", "s": 0.0, "e": 0.2}, {"w": "l'oubli", "s": 0.5, "e": 1.0}]
    assert timeline.anchor_frame(words, "oubli", 0.0, 2.0, "Sur l'oubli") == 15


def test_anchor_with_apostrophe_matches_split_retranscription():
    words = [{"w": "Sur", "s": 0.0, "e": 0.2}, {"w": "l", "s": 0.5, "e": 0.6}, {"w": "oubli", "s": 0.6, "e": 1.0}]
    assert timeline.anchor_frame(words, "l'oubli", 0.0, 2.0, "Sur l'oubli") == 15


def test_anchor_of_several_words_uses_first_word():
    words = [{"w": "Le", "s": 0.0, "e": 0.2}, {"w": "mur", "s": 0.4, "e": 0.7}, {"w": "de", "s": 0.8, "e": 0.9},
             {"w": "Berlin", "s": 1.0, "e": 1.5}]
    assert timeline.anchor_frame(words, "mur de Berlin", 0.0, 2.0, "Le mur de Berlin") == 12


def test_anchor_occurring_twice_first_wins():
    words = [{"w": "chat", "s": 0.2, "e": 0.4}, {"w": "et", "s": 0.5, "e": 0.6}, {"w": "chat", "s": 1.0, "e": 1.4}]
    assert timeline.anchor_frame(words, "chat", 0.0, 2.0, "chat et chat") == 6


def test_caption_groups_2_to_4_words_and_break_on_pause():
    words = [{"w": f"m{i}", "s": i * 0.3, "e": i * 0.3 + 0.2} for i in range(5)]
    words += [{"w": "apres", "s": 3.0, "e": 3.2}, {"w": "la", "s": 3.3, "e": 3.5}, {"w": "pause", "s": 3.6, "e": 3.9}]
    groups = timeline.caption_groups(words)
    sizes = [len(g["words"]) for g in groups]
    assert sizes == [3, 2, 3]
    assert all(1 <= s <= 4 for s in sizes)


def test_caption_groups_break_on_final_punctuation():
    words = [{"w": "Un", "s": 0.0, "e": 0.2}, {"w": "deux.", "s": 0.3, "e": 0.5}, {"w": "Trois", "s": 0.6, "e": 0.8},
             {"w": "quatre", "s": 0.9, "e": 1.1}]
    groups = timeline.caption_groups(words)
    assert [[w["w"] for w in g["words"]] for g in groups] == [["Un", "deux."], ["Trois", "quatre"]]


def test_caption_groups_frames_are_integers_and_do_not_overlap():
    words = [{"w": f"m{i}", "s": i * 0.21, "e": i * 0.21 + 0.19} for i in range(11)]
    groups = timeline.caption_groups(words)
    for g in groups:
        assert isinstance(g["from"], int) and isinstance(g["to"], int) and g["to"] > g["from"]
        for a, b in zip(g["words"], g["words"][1:]):
            assert a["to"] == b["from"]
        assert g["words"][-1]["to"] == g["to"]
    for a, b in zip(groups, groups[1:]):
        assert a["to"] <= b["from"]


def test_caption_groups_empty():
    assert timeline.caption_groups([]) == []


def build(job):
    return common.load_json(timeline.build_timeline(job, 1, 3))


def test_timeline_has_hook_first_outro_last_and_watermark(job_with_offsets):
    tl = build(job_with_offsets)
    assert tl["segments"][0]["kind"] == "hook" and tl["segments"][-1]["kind"] == "outro"
    assert tl["watermark"] == "@ideovideos" and tl["width"] == 1080 and tl["height"] == 1920
    assert tl["chapter"] == {"part": 1, "total": 3, "title": "L'oubli", "label": "Partie"}
    assert tl["fps"] == 30 and tl["lang"] == "fr" and tl["audio"] == "part.wav"
    assert common.read_status(job_with_offsets)["steps"]["timeline-01"]["ok"] is True


def test_single_part_plan_has_chapter_total_one(job_with_offsets):
    tl = common.load_json(timeline.build_timeline(job_with_offsets, 1, 1))
    assert tl["chapter"]["part"] == 1 and tl["chapter"]["total"] == 1


def test_timeline_segments_are_contiguous_and_cover_the_part(job_with_offsets):
    tl = build(job_with_offsets)
    segs = tl["segments"]
    assert segs[0]["from"] == 0
    for a, b in zip(segs, segs[1:]):
        assert a["to"] == b["from"]
    assert segs[-1]["to"] == tl["durationInFrames"]
    offsets = common.load_json(job_with_offsets / "parts" / "01" / "offsets.json")
    assert tl["durationInFrames"] == math.ceil(round(offsets[-1]["end"] * 30, 6))
    assert [s["kind"] for s in segs] == ["hook", "scene", "scene", "scene", "scene", "scene", "hook", "outro"]
    assert [s.get("type") for s in segs[1:-2]] == ["key-title", "shape-diagram", "fact-chips", "stack-list", "quote"]
    assert segs[-2]["props"]["text"] == "Et toi, tu relis tes cours ou tu les oublies ?"
    assert segs[0]["props"]["text"].startswith("Dis-moi")
    assert segs[-1]["props"]["text"] == "Si ça t'a plu, abonne-toi pour la prochaine !"


def test_timeline_items_anchor_on_found_and_missing_words(job_with_offsets):
    tl = build(job_with_offsets)
    scene = tl["segments"][2]
    offsets = common.load_json(job_with_offsets / "parts" / "01" / "offsets.json")
    start = offsets[2]["start"]
    lundi, jeudi = scene["items"]
    assert (lundi["el"], jeudi["el"]) == ("values.0", "values.3")
    assert lundi["at"] == round((start + 1.0 / 14) * 30)
    assert scene["from"] <= lundi["at"] < jeudi["at"] < scene["to"]
    assert scene["props"]["shape"] == "circle"


def test_timeline_captions_use_source_words_during_quote_and_none_during_sfx(job_with_offsets):
    tl = build(job_with_offsets)
    offsets = common.load_json(job_with_offsets / "parts" / "01" / "offsets.json")
    quote_clip = offsets[5]["clip"]
    sfx_clip = offsets[3]["clip"]
    in_quote = [g for g in tl["captions"] if quote_clip["start"] * 30 <= g["from"] < quote_clip["end"] * 30]
    texts = [w["w"] for g in in_quote for w in g["words"]]
    assert texts[0] == "Nous" and texts[-1] == "journée"
    assert not [g for g in tl["captions"] if sfx_clip["start"] * 30 <= g["from"] < sfx_clip["end"] * 30]
    first = tl["captions"][0]
    assert first["words"][0]["w"] == "Dis-moi" and first["from"] == 0
    for a, b in zip(tl["captions"], tl["captions"][1:]):
        assert a["to"] <= b["from"]


def test_timeline_is_idempotent(job_with_offsets):
    first = timeline.build_timeline(job_with_offsets, 1, 3).read_text(encoding="utf-8")
    assert timeline.build_timeline(job_with_offsets, 1, 3).read_text(encoding="utf-8") == first


def test_timeline_without_offsets_is_french_error(job_with_voice_fixtures):
    with pytest.raises(common.IdeoError, match="offsets"):
        timeline.build_timeline(job_with_voice_fixtures, 1, 3)
    assert common.read_status(job_with_voice_fixtures)["steps"]["timeline-01"]["ok"] is False


def test_first_item_of_a_scene_appears_within_nine_frames(job_with_offsets):
    from ideo import common as c

    plan = c.load_json(job_with_offsets / "plan.json")
    plan["parts"][0]["scenes"][1]["items"] = [{"el": "values.3", "on": "oublie"}, {"el": "values.0", "on": "rien"}]
    c.save_json(job_with_offsets / "plan.json", plan)
    tl = build(job_with_offsets)
    scene = tl["segments"][2]
    assert scene["items"][0]["at"] <= scene["from"] + 9
    assert scene["items"][0]["at"] <= scene["items"][1]["at"]


def test_numeric_anchor_is_accepted():
    words = [{"w": "En", "s": 0.0, "e": 0.2}, {"w": "1991", "s": 0.5, "e": 0.9}]
    assert timeline.anchor_frame(words, 1991, 0.0, 2.0, "En 1991") == 15


def test_captions_show_the_written_words(job_with_offsets):
    tl = build(job_with_offsets)
    shown = [w["w"] for g in tl["captions"] for w in g["words"]]
    assert "Dis-moi" in shown and "Aujourd'hui" in shown
    assert not any(w.startswith("'") or w == "-" for w in shown)


def test_quote_captions_use_the_text_of_the_plan(job_with_offsets):
    from ideo import common as c

    plan = c.load_json(job_with_offsets / "plan.json")
    text = plan["parts"][0]["scenes"][4]["props"]["text"]
    tl = build(job_with_offsets)
    offsets = c.load_json(job_with_offsets / "parts" / "01" / "offsets.json")
    clip = offsets[5]["clip"]
    in_quote = [g for g in tl["captions"] if clip["start"] * 30 <= g["from"] < clip["end"] * 30]
    assert [w["w"] for g in in_quote for w in g["words"]] == text.split()
    assert all(1 <= len(g["words"]) <= 4 for g in tl["captions"])


def test_object_state_first_item_keeps_its_own_word(job_with_offsets):
    from ideo import common as c

    plan = c.load_json(job_with_offsets / "plan.json")
    scene = plan["parts"][0]["scenes"][3]
    scene["type"] = "object-state"
    scene["props"] = {"object": "door", "states": ["fermée", "ouverte"]}
    scene["items"] = [{"el": "states.1", "on": "simples"}]
    c.save_json(job_with_offsets / "plan.json", plan)
    tl = build(job_with_offsets)
    seg = tl["segments"][4]
    assert seg["type"] == "object-state"
    assert seg["items"][0]["at"] > seg["from"] + 9


def words_at(texts_and_times):
    return [{"w": w, "s": s, "e": s + 0.2} for w, s in texts_and_times]


def test_sentence_starts_become_beats_except_the_first():
    say = "Il est parti. Elle reste ici ! Ensuite quoi ? Rien."
    words = align.script_words(say)
    seg = words_at(zip(words, [0.0, 0.3, 0.6, 1.0, 1.3, 1.6, 1.9, 2.2, 2.5]))
    beats = timeline.beat_frames(say, seg, 10.0, 3.0, 300, 400, [])
    assert beats == [round((10.0 + t) * 30) for t in (1.0, 1.9, 2.5)]


def test_no_sentence_break_no_beat_in_a_short_scene():
    say = "Une seule phrase assez courte pour tenir"
    seg = words_at([(w, i * 0.4) for i, w in enumerate(align.script_words(say))])
    assert timeline.beat_frames(say, seg, 0.0, 3.0, 0, 90, []) == []


def test_midpoint_beat_in_any_gap_over_four_seconds_on_a_word_start():
    say = "un deux trois quatre cinq six sept huit neuf dix onze douze treize"
    seg = words_at([(w, i * 1.0) for i, w in enumerate(align.script_words(say))])
    beats = timeline.beat_frames(say, seg, 0.0, 13.0, 0, 390, [])
    starts = {round(i * 30) for i in range(13)}
    assert beats and all(b in starts for b in beats)
    points = [0] + beats + [390]
    assert all(b - a <= 120 for a, b in zip(points, points[1:]))
    assert beats == sorted(beats)


def test_gaps_are_measured_between_items_and_beats_too():
    say = "un deux trois quatre cinq six sept huit neuf dix onze douze"
    seg = words_at([(w, i * 1.0) for i, w in enumerate(align.script_words(say))])
    beats = timeline.beat_frames(say, seg, 0.0, 12.0, 0, 360, [180])
    points = sorted([0, 180, 360] + beats)
    assert all(b - a <= 120 for a, b in zip(points, points[1:]))


def test_never_within_twenty_frames_of_an_item():
    say = "Une phrase. Une autre phrase. Encore une. Et la fin."
    words = align.script_words(say)
    seg = words_at([(w, i * 0.5) for i, w in enumerate(words)])
    plain = timeline.beat_frames(say, seg, 0.0, 6.0, 0, 180, [])
    assert plain
    item = plain[0] + 10
    beats = timeline.beat_frames(say, seg, 0.0, 6.0, 0, 180, [item])
    assert all(abs(b - item) >= 20 for b in beats)


def test_beats_are_inside_the_scene_and_stop_before_a_source_clip():
    say = "Une phrase. Une autre phrase. Encore une. Et la fin de la scene."
    seg = words_at([(w, i * 1.2) for i, w in enumerate(align.script_words(say))])
    beats = timeline.beat_frames(say, seg, 0.0, 14.0, 100, 300, [])
    assert all(100 < b < 300 for b in beats)


def test_proportional_fallback_when_word_counts_differ():
    say = "Une phrase. Une autre phrase."
    beats = timeline.beat_frames(say, [{"w": "x", "s": 0.0, "e": 1.0}], 0.0, 4.0, 0, 120, [])
    assert len(beats) == 1 and 40 <= beats[0] <= 80


def test_scene_segments_carry_increasing_beats_clear_of_items(job_with_offsets):
    tl = build(job_with_offsets)
    for seg in tl["segments"]:
        beats = seg.get("beats", [])
        assert beats == sorted(set(beats))
        assert all(seg["from"] < b < seg["to"] for b in beats)
        assert all(abs(b - i["at"]) >= 20 for b in beats for i in seg.get("items", []))
        if seg["kind"] != "scene":
            assert "beats" not in seg


def test_beats_follow_the_second_sentence_of_a_scene(job_with_offsets):
    from ideo import common as c

    plan = c.load_json(job_with_offsets / "plan.json")
    plan["parts"][0]["scenes"][3]["say"] = "Heureusement il existe des gestes simples. Voici le premier."
    c.save_json(job_with_offsets / "plan.json", plan)
    from tests.conftest import VOICE_WORDS, _timed_words

    words = ["Heureusement", "il", "existe", "des", "gestes", "simples.", "Voici", "le", "premier."]
    c.save_json(job_with_offsets / "parts" / "01" / "seg_04.words.json", _timed_words(words, 1.0))
    tl = build(job_with_offsets)
    offsets = c.load_json(job_with_offsets / "parts" / "01" / "offsets.json")
    seg = tl["segments"][4]
    assert seg["beats"][0] == round((offsets[4]["start"] + 6 * (1.0 / 9)) * 30)


def test_captions_show_the_space_before_high_punctuation_and_anchors_still_work(job_with_offsets):
    from ideo import common as c

    plan = c.load_json(job_with_offsets / "plan.json")
    plan["parts"][0]["scenes"][3]["say"] = "Heureusement il existe des gestes simples ! Voici le premier ?"
    plan["parts"][0]["scenes"][3]["items"] = [{"el": "items.1", "on": "simples"}]
    c.save_json(job_with_offsets / "plan.json", plan)
    from tests.conftest import _timed_words

    shown = align.script_words(plan["parts"][0]["scenes"][3]["say"])
    c.save_json(job_with_offsets / "parts" / "01" / "seg_04.words.json", _timed_words(shown, 1.0))
    tl = build(job_with_offsets)
    texts = [w["w"] for g in tl["captions"] for w in g["words"]]
    assert "simples !" in texts and "premier ?" in texts
    offsets = c.load_json(job_with_offsets / "parts" / "01" / "offsets.json")
    seg = tl["segments"][4]
    assert seg["items"][0]["at"] == min(round((offsets[4]["start"] + 5 * (1.0 / 9)) * 30), seg["from"] + 9)
    assert seg["items"][0]["at"] > seg["from"] + 5
