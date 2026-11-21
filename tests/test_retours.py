import pytest

from ideo import retours


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    return tmp_path


def text():
    return retours.path().read_text(encoding="utf-8")


def test_file_is_created_with_the_three_sections():
    retours.add(retours.SIGNALES, "[2026-11-21] (job) Un défaut")
    body = text()
    assert body.startswith("# Retours")
    assert body.index("## Défauts signalés") < body.index("## Défauts détectés") < body.index("## Dessins manquants")
    assert "- [ ] [2026-11-21] (job) Un défaut" in body


def test_entries_go_under_their_section_in_order():
    retours.add(retours.DETECTES, "deux")
    retours.add(retours.SIGNALES, "un")
    retours.add(retours.DETECTES, "trois")
    body = text()
    assert body.index("- [ ] un") < body.index("## Défauts détectés") < body.index("- [ ] deux") < body.index("- [ ] trois")


def test_unchecked_ignores_checked_entries():
    retours.add(retours.SIGNALES, "a")
    retours.add(retours.SIGNALES, "b")
    retours.path().write_text(text().replace("- [ ] a", "- [x] a"), encoding="utf-8")
    assert retours.unchecked() == ["b"]
    assert retours.unchecked(retours.DETECTES) == []


def test_wishes_count_when_they_come_back_ignoring_case_and_accents():
    retours.add_wish("Drapeau américain")
    retours.add_wish("drapeau AMERICAIN")
    retours.add_wish("carte du monde")
    wishes = retours.wishes()
    assert wishes[0] == ("Drapeau américain", 2) and ("carte du monde", 1) in wishes
    assert "- [ ] Drapeau américain (×2)" in text()


def test_wishes_sorted_by_counter():
    retours.add_wish("a une")
    retours.add_wish("b deux")
    retours.add_wish("b deux")
    assert [w for w, _ in retours.wishes()] == ["b deux", "a une"]


def test_checked_wish_that_returns_makes_a_new_entry():
    retours.add_wish("globe de nuit")
    retours.path().write_text(text().replace("- [ ] globe de nuit", "- [x] globe de nuit"), encoding="utf-8")
    retours.add_wish("globe de nuit")
    assert retours.wishes() == [("globe de nuit", 1)]


def test_detected_defect_is_added_once_while_unchecked():
    assert retours.add_detected("silence-long", "job1", "Un silence")
    assert not retours.add_detected("silence-long", "job2", "Un autre silence")
    assert "- [ ] `silence-long` (job1) Un silence" in text()
    retours.path().write_text(text().replace("- [ ] `silence-long`", "- [x] `silence-long`"), encoding="utf-8")
    assert retours.add_detected("silence-long", "job3", "Encore")


def test_count_unchecked_over_all_sections():
    retours.add(retours.SIGNALES, "a")
    retours.add(retours.DETECTES, "b")
    retours.add_wish("c")
    assert retours.count_unchecked() == 3


def test_old_format_lines_are_migrated_as_unchecked_signals():
    retours.path().write_text("# Retours\n\nIntro.\n\n- [2026-11-01] (j) Ancien défaut\n", encoding="utf-8")
    retours.add(retours.SIGNALES, "nouveau")
    assert retours.unchecked(retours.SIGNALES) == ["[2026-11-01] (j) Ancien défaut", "nouveau"]


def test_unreadable_file_never_raises(home):
    retours.path().mkdir()
    assert retours.unchecked() == [] and retours.count_unchecked() == 0
