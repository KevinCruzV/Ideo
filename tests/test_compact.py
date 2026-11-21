import pytest

from ideo import compact

INFO = {"title": "T", "channel": "C", "duration": 60}


def test_compact_paragraphs_on_pause_and_length():
    words = [{"w": "a", "s": i * 0.3, "e": i * 0.3 + 0.2} for i in range(130)]
    text = compact.build(words, [], INFO)[0]
    paras = [line for line in text.splitlines() if line.startswith("[")]
    assert len(paras) == 3 and paras[0].startswith("[0:00]")


def test_compact_breaks_on_pause():
    words = [{"w": "a", "s": 0.0, "e": 0.5}, {"w": "b", "s": 0.6, "e": 1.0}, {"w": "c", "s": 3.0, "e": 3.4}]
    text = compact.build(words, [], INFO)[0]
    paras = [line for line in text.splitlines() if line.startswith("[")]
    assert paras == ["[0:00] a b", "[0:03] c"]


def test_compact_inserts_sfx_marker():
    words = [{"w": "a", "s": 0.0, "e": 9.5}, {"w": "b", "s": 13.0, "e": 14.0}]
    sfx = [{"at": "0:10", "s": 10.0, "e": 12.0}]
    lines = compact.build(words, sfx, INFO)[0].splitlines()
    assert "[son 0:10 2.0s]" in lines
    assert lines.index("[son 0:10 2.0s]") < lines.index("[0:13] b")


def test_compact_has_no_word_timings():
    words = [{"w": "bonjour", "s": 1.23, "e": 1.5}]
    assert "1.23" not in compact.build(words, [], INFO)[0]


def test_compact_header_with_chapters():
    info = {**INFO, "language": "fr", "chapters": [
        {"start_time": 0, "title": "Intro"}, {"start_time": 125, "title": "Suite"}]}
    text = compact.build([{"w": "a", "s": 0, "e": 1}], [], info)[0]
    head = text.split("\n\n")[0]
    assert "T" in head and "C" in head and "1:00" in head and "fr" in head
    assert "- 0:00 Intro" in head and "- 2:05 Suite" in head


def test_compact_header_without_chapters():
    text = compact.build([{"w": "a", "s": 0, "e": 1}], [], {**INFO, "chapters": None})[0]
    assert "- " not in text


def para_words(start, text, step=0.4):
    return [{"w": w, "s": round(start + i * step, 2), "e": round(start + i * step + 0.3, 2)}
            for i, w in enumerate(text.split())]


SPEECH = (para_words(0, "La lumière du soleil est blanche et le ciel est bleu")
          + para_words(10, "Cette vidéo est sponsorisée par une marque de matelas avec un code promo")
          + para_words(20, "Leurs matelas sont très confortables pour bien dormir")
          + para_words(90, "Revenons au ciel qui diffuse le bleu partout"))


def test_sponsorblock_segment_replaces_paragraphs():
    info = {**INFO, "skip": [{"s": 9.5, "e": 25.0, "kind": "sponsor"}]}
    text, hidden = compact.build(SPEECH, [{"at": "0:22", "s": 22.0, "e": 23.0}], info)
    assert "[passage sponsorisé 0:10 à 0:23, ignoré]" in text
    assert "matelas" not in text and "[son 0:22" not in text
    assert "[0:00] La lumière" in text and "[1:30] Revenons" in text
    assert hidden == [{"s": 10.0, "e": 23.1, "probable": False}]


def test_paragraph_mostly_outside_segment_is_kept():
    info = {**INFO, "skip": [{"s": 4.0, "e": 5.0, "kind": "selfpromo"}]}
    text, hidden = compact.build(SPEECH, [], info)
    assert "[0:00] La lumière" in text and hidden == []


RUN = (para_words(0, "La lumière du soleil est blanche et le ciel est bleu")
       + para_words(10, "Cette vidéo est sponsorisée par une marque de matelas")
       + para_words(15, "Leurs matelas sont très confortables pour bien dormir")
       + para_words(25, "Revenons au ciel qui diffuse le bleu partout"))


def test_keyword_fallback_window_ends_at_first_long_pause():
    text, hidden = compact.build(RUN, [], INFO)
    assert "[passage probablement sponsorisé 0:10 à 0:18, ignoré]" in text
    assert "matelas" not in text and "[0:25] Revenons" in text
    assert hidden == [{"s": 10.0, "e": 18.1, "probable": True}]


def test_keyword_fallback_window_stops_after_sixty_seconds():
    words = para_words(0, "Cette vidéo est sponsorisée par Acme et ses matelas")
    for k in range(1, 15):
        words += para_words(k * 5.2, "Acme vend des matelas très doux pour bien dormir")
    text, hidden = compact.build(words, [], INFO)
    assert hidden == [{"s": 0.0, "e": 60.7, "probable": True}]
    assert "[1:02] Acme vend" in text


def test_no_fallback_when_sponsorblock_has_data():
    info = {**INFO, "skip": [{"s": 200.0, "e": 210.0, "kind": "sponsor"}]}
    text, hidden = compact.build(SPEECH, [], info)
    assert "matelas" in text and hidden == []


def test_sponsor_wording_in_both_languages():
    assert compact.is_sponsor_text("This video is brought to you by Acme")
    assert compact.is_sponsor_text("utilise le CODE PROMO ciel pour dix pour cent")
    assert compact.is_sponsor_text("Today 's sponsor is Acme")
    assert compact.is_sponsor_text("Cette vidéo est sponsorisée par Acme")
    assert not compact.is_sponsor_text("Le ciel est bleu à cause de la diffusion")


@pytest.mark.parametrize("text", [
    "cette vidéo n'est pas sponsorisée",
    "Cette vidéo n'est pas sponsorisée par une marque",
    "This video is not sponsored by anyone",
    "we use code to draw the sky",
    "Use code SKY for ten percent off",
    "en partenariat avec le CNRS",
    "la source est en lien en description",
    "the paper is linked, link in the description",
    "brought to you by the same team as last year",
    "c'est sponsorisé, mais pas ici",
])
def test_weak_or_negated_wording_is_not_a_sponsor(text):
    assert not compact.is_sponsor_text(text)


LONG_INFO = {"title": "T", "channel": "C", "duration": 1000, "language": "fr"}
BODY = (para_words(0, "Le ciel est bleu parce que la lumière se diffuse dans l'air")
        + para_words(500, "La conclusion est que la physique explique les couleurs")
        + para_words(930, "Cette partie reste dans la vidéo et parle de physique")
        + para_words(960, "Merci d 'avoir regardé, abonne -toi et active la cloche")
        + para_words(975, "Retrouve -moi sur Instagram et sur Patreon, à bientôt"))


def test_end_of_video_with_strong_keywords_is_replaced():
    text, hidden = compact.build(BODY, [], LONG_INFO)
    assert "[fin de vidéo, ignorée]" in text
    assert "Merci" not in text and "Instagram" not in text and "[15:30] Cette partie" in text
    assert hidden[-1]["end"] is True and hidden[-1]["s"] == 960.0


def test_end_zone_needs_a_strong_keyword():
    words = BODY[:-22]
    words = words + para_words(960, "Voilà la dernière idée, une jolie conclusion sur la lumière")
    text, hidden = compact.build(words, [], LONG_INFO)
    assert "[fin de vidéo" not in text and "end" not in str(hidden)


def test_keywords_before_the_last_eight_percent_are_kept():
    words = para_words(100, "Abonne -toi à la chaîne, mais ce n'est pas la fin") + BODY[:-22]
    words = sorted(words, key=lambda w: w["s"])
    text, hidden = compact.build(words, [], LONG_INFO)
    assert "Abonne" in text and "[fin de vidéo" not in text


@pytest.mark.parametrize("phrase", [
    "Please like and subscribe to the channel", "Thanks for watching, see you soon",
    "Suscríbete y activa la campana", "Abonniere den Kanal und lass ein Like da",
    "Iscriviti al canale e segui su Instagram", "Inscreva-se no canal", "Abonneer je op het kanaal",
    "Zasubskrybuj kanał", "Kanala abone ol",
])
def test_end_keywords_in_the_supported_languages(phrase):
    assert compact.is_end_text(phrase)


def test_end_keywords_are_whole_words():
    assert not compact.is_end_text("This is likely to be unlike the rest")
    assert not compact.is_end_text("Le ciel est bleu à cause de la diffusion")


def test_header_has_the_advised_duration():
    text = compact.build(BODY, [], LONG_INFO)[0]
    assert "Durée conseillée : 120 à 180 s (environ 408 à 612 mots de say)." in text.split("\n\n")[0]


def prepared_job(tmp_path, monkeypatch):
    from ideo import common

    job = tmp_path / "job"
    job.mkdir()
    common.save_json(job / "words.json", BODY)
    common.save_json(job / "info.json", {"title": "T", "channel": "C", "duration": 1000})
    (job / "lang.txt").write_text("fr", encoding="utf-8")
    monkeypatch.setattr(compact.sfx_mod, "rms_db_per_second", lambda path: [])
    monkeypatch.setattr(compact.sfx_mod, "find_sfx", lambda rms, words: [])
    return job


def test_transcript_cache_is_reused_at_the_same_version(tmp_path, monkeypatch):
    job = prepared_job(tmp_path, monkeypatch)
    compact.prepare_transcript(job)
    (job / "transcript_compact.md").write_text("édité", encoding="utf-8")
    compact.prepare_transcript(job)
    assert (job / "transcript_compact.md").read_text(encoding="utf-8") == "édité"


def test_transcript_is_rebuilt_when_the_cache_version_is_old(tmp_path, monkeypatch):
    from ideo import common

    job = prepared_job(tmp_path, monkeypatch)
    compact.prepare_transcript(job)
    skip = common.load_json(job / "skip.json")
    assert skip["version"] == compact.TRANSCRIPT_VERSION
    del skip["version"]
    common.save_json(job / "skip.json", skip)
    (job / "transcript_compact.md").write_text("ancien format", encoding="utf-8")
    compact.prepare_transcript(job)
    text = (job / "transcript_compact.md").read_text(encoding="utf-8")
    assert "Durée conseillée" in text and "[fin de vidéo, ignorée]" in text
