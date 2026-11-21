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
