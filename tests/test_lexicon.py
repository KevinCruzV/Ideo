import json

import pytest

from ideo import cli, common, lexicon


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    return tmp_path


def write(home, data):
    path = lexicon.path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_no_file_changes_nothing():
    assert lexicon.apply("Face à face", "fr") == "Face à face"


def test_whole_words_without_case_keeping_punctuation(home):
    write(home, {"fr": {"face": "fasse"}})
    assert lexicon.apply("Face à face : le monde.", "fr") == "Fasse à fasse : le monde."
    assert lexicon.apply("FACE au mur, face!", "fr") == "FASSE au mur, fasse!"
    assert lexicon.apply("surface, faces, interface", "fr") == "surface, faces, interface"


def test_elision_and_hyphen_are_word_boundaries(home):
    write(home, {"fr": {"image": "image"}})
    write(home, {"fr": {"face": "fasse", "image": "imaje"}})
    assert lexicon.apply("l'image face-à-face", "fr") == "l'imaje fasse-à-fasse"


def test_languages_are_separate(home):
    write(home, {"fr": {"face": "fasse"}, "en": {"data": "dayta"}})
    assert lexicon.apply("face data", "fr") == "fasse data"
    assert lexicon.apply("face data", "en") == "face dayta"
    assert lexicon.apply("face", "de") == "face"


def test_word_count_is_preserved(home):
    write(home, {"fr": {"face": "fasse"}})
    text = "Face à face, c'est la face cachée !"
    assert len(lexicon.apply(text, "fr").split()) == len(text.split())


def test_add_creates_and_replaces_entries(home):
    lexicon.add("face", "fasse")
    lexicon.add("Place", "plasse")
    lexicon.add("face", "fass")
    assert common.load_json(lexicon.path()) == {"fr": {"face": "fass", "place": "plasse"}}


def test_add_for_another_language(home):
    lexicon.add("data", "dayta", "en")
    assert common.load_json(lexicon.path())["en"] == {"data": "dayta"}


@pytest.mark.parametrize("word,spoken", [("", "fasse"), ("face", ""), ("fa ce", "fasse"), ("face", "fa sse"), ("  ", "x")])
def test_bad_entries_are_refused(word, spoken):
    with pytest.raises(common.IdeoError):
        lexicon.add(word, spoken)
    assert not lexicon.path().exists()


def test_unreadable_file_is_ignored_for_reading(home):
    lexicon.path().parent.mkdir(parents=True, exist_ok=True)
    lexicon.path().write_text("{pas du json", encoding="utf-8")
    assert lexicon.apply("face", "fr") == "face"
    with pytest.raises(common.IdeoError, match="prononciation.json"):
        lexicon.add("face", "fasse")


def test_cli_learn_prononciation(home, capsys):
    assert cli.main(["learn", "--prononciation", "face=fasse"]) == 0
    assert capsys.readouterr().out.strip() == "OK learn : prononciation enregistrée (face se dira « fasse »)"
    assert cli.main(["learn", "--prononciation", "data=dayta", "--lang", "en"]) == 0
    assert common.load_json(lexicon.path()) == {"fr": {"face": "fasse"}, "en": {"data": "dayta"}}


@pytest.mark.parametrize("argv", [["learn", "--prononciation"], ["learn", "--prononciation", "face"],
                                  ["learn", "--prononciation", "=x"], ["learn", "--prononciation", "fa ce=x"],
                                  ["learn", "--prononciation", "a=b", "--lang"], ["learn", "--prononciation", "a=b", "--lang", "xx", "y"]])
def test_cli_learn_prononciation_errors_are_one_line(argv, capsys):
    assert cli.main(argv) == 1
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and out[0].startswith("ERREUR ")


def test_repo_lexicon_starts_with_face_and_is_valid(monkeypatch):
    monkeypatch.delenv("IDEO_HOME")
    data = json.loads((common.REPO_ROOT / "skills" / "ideo" / "references" / "prononciation.json").read_text(encoding="utf-8"))
    assert data["fr"]["face"] == "fasse"
    for words in data.values():
        for word, spoken in words.items():
            assert word == word.lower() and " " not in word and " " not in spoken and spoken
