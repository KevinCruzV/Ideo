import json

import pytest

from ideo import cli, common, photo, plan_check, render, timeline

FREE_META = {
    "LicenseShortName": {"value": "CC BY-SA 4.0"},
    "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"},
    "Artist": {"value": '<a href="//x">Jeanne <b>Martin</b></a>'},
}


class Wiki:
    def __init__(self, license_name="CC BY-SA 4.0", human=True, image=True, mime="image/jpeg"):
        self.meta = {**FREE_META, "LicenseShortName": {"value": license_name}}
        self.human, self.image, self.mime = human, image, mime
        self.downloads = []

    def get_json(self, url):
        if "wikipedia.org" in url:
            if not self.image:
                return {"query": {"pages": [{"title": "X", "missing": True}]}}
            return {"query": {"pages": [{"title": "Ada Lovelace", "pageimage": "Ada.jpg", "pageprops": {"wikibase_item": "Q7"}}]}}
        if "wikidata.org" in url:
            kind = "Q5" if self.human else "Q42"
            claim = {"mainsnak": {"datavalue": {"value": {"id": kind}}}}
            return {"entities": {"Q7": {"claims": {"P31": [claim]}}}}
        return {"query": {"pages": [{"imageinfo": [{"thumburl": "https://upload.example/ada.jpg", "url": "https://upload.example/o.jpg",
                                                     "descriptionurl": "https://commons.example/File:Ada.jpg", "mime": self.mime,
                                                     "extmetadata": self.meta}]}]}}

    def download(self, url, dest):
        self.downloads.append(url)
        dest.write_bytes(b"\xff\xd8fake")


@pytest.fixture
def wiki(monkeypatch):
    def blocked(*a, **k):
        raise AssertionError("aucun appel réseau dans les tests")

    monkeypatch.setattr("urllib.request.urlopen", blocked)
    state = Wiki()
    monkeypatch.setattr(photo, "_get_json", state.get_json)
    monkeypatch.setattr(photo, "_download", state.download)
    return state


@pytest.fixture
def job(tmp_path):
    path = tmp_path / "job"
    path.mkdir()
    (path / "lang.txt").write_text("fr", encoding="utf-8")
    return path


@pytest.mark.parametrize("name,ok", [
    ("Public domain", True), ("CC0", True), ("CC BY 4.0", True), ("CC BY-SA 3.0", True), ("CC BY-SA 2.5", True),
    ("CC BY-NC 4.0", False), ("CC BY-ND 4.0", False), ("CC BY-NC-SA 3.0", False), ("Fair use", False), ("", False),
    ("All rights reserved", False),
])
def test_only_free_licenses_are_accepted(name, ok):
    assert photo.free_license(name) is ok


def test_a_free_photo_is_downloaded_with_its_credit(job, wiki):
    line = photo.run(job, "Ada Lovelace")
    assert line.startswith("OK photo : Ada Lovelace, CC BY-SA 4.0, Jeanne Martin")
    assert (job / "photo.jpg").read_bytes().startswith(b"\xff\xd8")
    data = common.load_json(job / "photo.json")
    assert data["author"] == "Jeanne Martin" and data["license"] == "CC BY-SA 4.0"
    assert data["source_url"] == "https://commons.example/File:Ada.jpg"
    sources = (job / "out" / "sources.md").read_text(encoding="utf-8")
    assert "Photo : Ada Lovelace, Jeanne Martin, CC BY-SA 4.0" in sources and "File:Ada.jpg" in sources


def test_credit_is_not_duplicated_and_survives_the_full_sources_file(job, wiki):
    photo.run(job, "Ada Lovelace")
    photo.write_credit(job)
    assert (job / "out" / "sources.md").read_text(encoding="utf-8").count("Photo : ") == 1
    common.save_json(job / "info.json", {"id": "abc"})
    common.save_json(job / "plan.json", {"parts": [{"n": 1, "title": "T", "scenes": [{"type": "stamp", "say": "Un deux.", "src": "0:10"}]}]})
    assert "Photo : Ada Lovelace" in render.write_sources(job).read_text(encoding="utf-8")


@pytest.mark.parametrize("license_name", ["CC BY-NC 4.0", "All rights reserved", "Fair use"])
def test_a_non_free_license_downloads_nothing(job, wiki, license_name):
    wiki.meta["LicenseShortName"] = {"value": license_name}
    assert photo.run(job, "Ada Lovelace") == "OK photo : aucune photo libre"
    assert wiki.downloads == [] and not list(job.glob("photo.*")) and not (job / "out").exists()


def test_no_page_image_or_not_a_person_downloads_nothing(job, wiki):
    wiki.image = False
    assert photo.run(job, "Personne") == photo.NONE
    wiki.image, wiki.human = True, False
    assert photo.run(job, "Un objet") == photo.NONE
    assert wiki.downloads == []


def test_an_unsupported_image_type_is_ignored(job, wiki):
    wiki.mime = "image/svg+xml"
    assert photo.run(job, "Ada Lovelace") == photo.NONE


def test_a_dark_plan_never_gets_a_photo(job, wiki):
    common.save_json(job / "plan.json", {"mood": "dark", "parts": []})
    with pytest.raises(common.IdeoError, match="fait divers"):
        photo.run(job, "Ada Lovelace")
    assert wiki.downloads == []


def test_a_new_search_replaces_the_previous_photo(job, wiki):
    photo.run(job, "Ada Lovelace")
    wiki.image = False
    assert photo.run(job, "Personne") == photo.NONE
    assert photo.stored(job) is None and not list(job.glob("photo.*"))


def test_network_failure_is_a_clear_error(job, monkeypatch):
    def boom(url):
        raise OSError("réseau coupé")

    monkeypatch.setattr(photo, "_get_json", boom)
    with pytest.raises(common.IdeoError, match="injoignable"):
        photo.run(job, "Ada Lovelace")


def test_command_line(monkeypatch):
    assert cli.parse(["photo", "job1", "Ada", "Lovelace"]) == ("photo", "job1", None, {"name": "Ada Lovelace"})
    with pytest.raises(cli.UsageError):
        cli.parse(["photo", "job1"])


def person_scene(src, **props):
    return {"type": "person-card", "say": "Le savant Hermann Ebbinghaus a mesuré lui-même sa mémoire.",
            "props": {"name": "Hermann Ebbinghaus", **props}, "items": [{"el": "name", "on": "Ebbinghaus"}], "src": src}


def test_check_refuses_photo_without_a_photo_in_the_job(job_with_fixtures):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["parts"][0]["scenes"].append(person_scene(plan["parts"][0]["scenes"][0]["src"], photo=True))
    common.save_json(job_with_fixtures / "plan.json", plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("« photo » demande une photo libre" in e for e in errors)
    common.save_json(job_with_fixtures / "photo.json", {"person": "Hermann Ebbinghaus", "extension": "jpg"})
    (job_with_fixtures / "photo.jpg").write_bytes(b"x")
    assert not [e for e in plan_check.check_plan(job_with_fixtures) if "photo" in e]
    plan["mood"] = "dark"
    common.save_json(job_with_fixtures / "plan.json", plan)
    assert any("pas de photo dans un fait divers" in e for e in plan_check.check_plan(job_with_fixtures))
    del plan["mood"]
    plan["parts"][0]["scenes"][-1]["props"]["name"] = "Marie Curie"
    common.save_json(job_with_fixtures / "plan.json", plan)
    assert any("la photo du job est celle de Hermann Ebbinghaus" in e for e in plan_check.check_plan(job_with_fixtures))


def test_timeline_stages_the_photo_and_shares_the_look_between_cards():
    scenes = {
        "seg_01": person_scene("0:10", hat="kepi", facial="moustache", photo=True),
        "seg_02": {"type": "stamp", "say": "x", "props": {"text": "x"}},
        "seg_03": person_scene("0:20"),
        "seg_04": {**person_scene("0:30"), "props": {"name": "Autre Personne"}},
        "seg_05": person_scene("0:40", hat="top-hat"),
    }
    shared = timeline._share_looks(scenes)
    assert shared["seg_03"]["props"]["hat"] == "kepi" and shared["seg_03"]["props"]["facial"] == "moustache"
    assert "hat" not in shared["seg_04"]["props"]
    assert shared["seg_05"]["props"]["hat"] == "top-hat"
    assert timeline._with_photo(shared["seg_01"], "photo.jpg")["props"]["photo"] == "photo.jpg"
    assert "photo" not in timeline._with_photo(shared["seg_01"], None)["props"]
    assert timeline._with_photo(shared["seg_03"], "photo.jpg") is shared["seg_03"]


def test_the_photo_is_copied_next_to_the_part_audio(job, tmp_path):
    out = tmp_path / "part"
    out.mkdir()
    assert timeline._stage_photo(job, out) is None
    common.save_json(job / "photo.json", {"extension": "png"})
    (job / "photo.png").write_bytes(b"png")
    assert timeline._stage_photo(job, out) == "photo.png"
    assert (out / "photo.png").read_bytes() == b"png"
