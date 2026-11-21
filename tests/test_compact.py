import pytest

from ideo import compact

INFO = {"title": "T", "channel": "C", "duration": 60}


def test_compact_paragraphs_on_pause_and_length():
    words = [{"w": "a", "s": i * 0.3, "e": i * 0.3 + 0.2} for i in range(130)]
    text = compact.compact(words, [], INFO)
    paras = [line for line in text.splitlines() if line.startswith("[")]
    assert len(paras) == 3 and paras[0].startswith("[0:00]")


def test_compact_breaks_on_pause():
    words = [{"w": "a", "s": 0.0, "e": 0.5}, {"w": "b", "s": 0.6, "e": 1.0}, {"w": "c", "s": 3.0, "e": 3.4}]
    text = compact.compact(words, [], INFO)
    paras = [line for line in text.splitlines() if line.startswith("[")]
    assert paras == ["[0:00] a b", "[0:03] c"]


def test_compact_inserts_sfx_marker():
    words = [{"w": "a", "s": 0.0, "e": 9.5}, {"w": "b", "s": 13.0, "e": 14.0}]
    sfx = [{"at": "0:10", "s": 10.0, "e": 12.0}]
    lines = compact.compact(words, sfx, INFO).splitlines()
    assert "[son 0:10 2.0s]" in lines
    assert lines.index("[son 0:10 2.0s]") < lines.index("[0:13] b")


def test_compact_has_no_word_timings():
    words = [{"w": "bonjour", "s": 1.23, "e": 1.5}]
    assert "1.23" not in compact.compact(words, [], INFO)


def test_compact_header_with_chapters():
    info = {**INFO, "language": "fr", "chapters": [
        {"start_time": 0, "title": "Intro"}, {"start_time": 125, "title": "Suite"}]}
    text = compact.compact([{"w": "a", "s": 0, "e": 1}], [], info)
    head = text.split("\n\n")[0]
    assert "T" in head and "C" in head and "1:00" in head and "fr" in head
    assert "- 0:00 Intro" in head and "- 2:05 Suite" in head


def test_compact_header_without_chapters():
    text = compact.compact([{"w": "a", "s": 0, "e": 1}], [], {**INFO, "chapters": None})
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
