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
        self.title = "Ada Lovelace"
        self.kind_id = "Q5"
        self.downloads = []
        self.search = []
        self.searches = 0

    def get_json(self, url):
        if "wikipedia.org" in url and "gsrsearch" in url:
            self.searches += 1
            return {"query": {"pages": self.search}}
        if "wikipedia.org" in url:
            if not self.image:
                return {"query": {"pages": [{"title": "X", "missing": True}]}}
            return {"query": {"pages": [{"title": self.title, "pageimage": "Ada.jpg", "pageprops": {"wikibase_item": "Q7"}}]}}
        if "wikidata.org" in url:
            kind = self.kind_id if self.human else "Q42"
            claim = {"mainsnak": {"datavalue": {"value": {"id": kind}}}}
            return {"entities": {"Q7": {"claims": {"P31": [claim]}}}}
        return {"query": {"pages": [{"imageinfo": [{"thumburl": "https://upload.example/ada.jpg", "url": "https://upload.example/o.jpg",
                                                     "descriptionurl": "https://commons.example/File:Ada.jpg", "mime": self.mime,
                                                     "extmetadata": self.meta}]}]}}

    def download(self, url, dest):
        self.downloads.append(url)
        dest.write_bytes(b"\xff\xd8fake")


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(photo.time, "sleep", lambda seconds: None)


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
    assert (job / "photo-ada-lovelace.jpg").read_bytes().startswith(b"\xff\xd8")
    data = common.load_json(job / "photo-ada-lovelace.json")
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


def test_a_new_search_for_the_same_person_replaces_the_previous_photo(job, wiki):
    photo.run(job, "Ada Lovelace")
    wiki.image = False
    assert photo.run(job, "Ada Lovelace") == photo.NONE
    assert photo.all_stored(job) == [] and not list(job.glob("photo*.*"))


def test_each_person_keeps_their_own_photo(job, wiki):
    photo.run(job, "Ada Lovelace")
    wiki.title = "Charles Babbage"
    photo.run(job, "Charles Babbage")
    assert sorted(p["person"] for p in photo.all_stored(job)) == ["Ada Lovelace", "Charles Babbage"]
    assert (job / "photo-ada-lovelace.jpg").exists() and (job / "photo-charles-babbage.jpg").exists()
    wiki.image = False
    assert photo.run(job, "Quelqu'un") == photo.NONE
    assert len(photo.all_stored(job)) == 2
    wiki.image = True
    wiki.title = "Charles Babbage"
    photo.run(job, "charles BABBAGE")
    assert len(photo.all_stored(job)) == 2


def test_add_manual_stores_a_local_photo_with_its_credit(job, tmp_path):
    local = tmp_path / "portrait.jpg"
    local.write_bytes(b"\xff\xd8fake")
    result = photo.add_manual(job, "Jeanne Martin", local, "Collection personnelle, 2024")
    assert result.startswith("OK photo : ")
    stored = photo.all_stored(job)
    assert len(stored) == 1 and stored[0]["person"] == "Jeanne Martin" and stored[0]["image"] == "photo-jeanne-martin.jpg"
    assert (job / "photo-jeanne-martin.jpg").read_bytes() == b"\xff\xd8fake"
    assert stored[0]["kind"] == photo.PERSON
    lines = photo.credit_lines(job)
    assert len(lines) == 1 and "Jeanne Martin" in lines[0] and "Collection personnelle, 2024" in lines[0]


def test_add_manual_accepts_png_and_webp(job, tmp_path):
    png = tmp_path / "logo.png"
    png.write_bytes(b"\x89PNGfake")
    photo.add_manual(job, "Marque X", png, "site officiel")
    assert (job / "photo-marque-x.png").exists()


def test_add_manual_refuses_an_unknown_extension(job, tmp_path):
    bad = tmp_path / "scan.pdf"
    bad.write_bytes(b"%PDF")
    with pytest.raises(common.IdeoError, match="format"):
        photo.add_manual(job, "Jeanne Martin", bad, "source")


def test_add_manual_refuses_a_missing_file(job, tmp_path):
    with pytest.raises(common.IdeoError, match="introuvable"):
        photo.add_manual(job, "Jeanne Martin", tmp_path / "absent.jpg", "source")


def test_add_manual_refuses_an_empty_name_or_source(job, tmp_path):
    local = tmp_path / "portrait.jpg"
    local.write_bytes(b"\xff\xd8fake")
    with pytest.raises(common.IdeoError):
        photo.add_manual(job, "  ", local, "source")
    with pytest.raises(common.IdeoError):
        photo.add_manual(job, "Jeanne Martin", local, "  ")


def test_add_manual_replaces_the_previous_photo_of_the_same_person(job, tmp_path):
    first = tmp_path / "a.jpg"
    first.write_bytes(b"first")
    second = tmp_path / "b.jpg"
    second.write_bytes(b"second")
    photo.add_manual(job, "Jeanne Martin", first, "source 1")
    photo.add_manual(job, "jeanne martin", second, "source 2")
    assert len(photo.all_stored(job)) == 1
    assert (job / "photo-jeanne-martin.jpg").read_bytes() == b"second"


def test_every_photo_has_its_credit(job, wiki):
    photo.run(job, "Ada Lovelace")
    wiki.title = "Charles Babbage"
    photo.run(job, "Charles Babbage")
    lines = photo.credit_lines(job)
    assert len(lines) == 2 and lines[0].startswith("Photo : Ada Lovelace") and lines[1].startswith("Photo : Charles Babbage")
    photo.write_credit(job)
    photo.write_credit(job)
    sources = (job / "out" / "sources.md").read_text(encoding="utf-8")
    assert sources.count("Photo : ") == 2
    common.save_json(job / "info.json", {"id": "abc"})
    common.save_json(job / "plan.json", {"parts": [{"n": 1, "title": "T", "scenes": [{"type": "stamp", "say": "Un deux.", "src": "0:10"}]}]})
    written = render.write_sources(job).read_text(encoding="utf-8")
    assert "Photo : Ada Lovelace" in written and "Photo : Charles Babbage" in written


def test_an_old_job_with_a_single_photo_file_still_works(job):
    common.save_json(job / "photo.json", {"person": "Marie Curie", "title": "Marie Curie", "author": "A", "license": "CC0", "source_url": "u", "extension": "png"})
    (job / "photo.png").write_bytes(b"png")
    assert [p["image"] for p in photo.all_stored(job)] == ["photo.png"]
    assert photo.credit_lines(job) == ["Photo : Marie Curie, A, CC0, u"]


def test_a_card_gets_the_photo_with_the_best_name_overlap():
    photos = [{"person": "Marie Curie", "image": "photo-marie-curie.jpg"}, {"person": "Pierre Curie", "image": "photo-pierre-curie.jpg"}]
    assert photo.match(photos, "Pierre Curie")["image"] == "photo-pierre-curie.jpg"
    assert photo.match(photos, "Marie Skłodowska-Curie")["image"] == "photo-marie-curie.jpg"
    assert photo.match(photos, "Curie") is None
    assert photo.match(photos, "Albert Einstein") is None
    assert photo.match(photos[:1], "Mme Curie")["image"] == "photo-marie-curie.jpg"
    assert photo.match([], "Marie Curie") is None
    gaulle = [{"person": "Charles de Gaulle", "image": "photo-charles-de-gaulle.jpg"}]
    assert photo.match(gaulle, "Simone de Beauvoir") is None
    assert photo.match(gaulle, "de Gaulle")["image"] == "photo-charles-de-gaulle.jpg"


def test_network_failure_is_a_clear_error(job, monkeypatch):
    def boom(url):
        raise OSError("réseau coupé")

    monkeypatch.setattr(photo, "_get_json", boom)
    with pytest.raises(common.IdeoError, match="injoignable"):
        photo.run(job, "Ada Lovelace")


def hit(title, index=1, image="Ada.jpg"):
    page = {"title": title, "index": index, "pageprops": {"wikibase_item": "Q7"}}
    if image:
        page["pageimage"] = image
    return page


def test_a_search_finds_the_page_when_the_exact_title_has_no_image(job, wiki):
    original = wiki.get_json

    def get_json(url):
        if "wikipedia.org" in url and "gsrsearch" not in url:
            return {"query": {"pages": [{"title": "Gérard Mulliez", "missing": True}]}}
        return original(url)

    wiki.search = [hit("Gérard Mulliez (homonyme)", 2, None), hit("Gérard Mulliez", 1)]
    photo._get_json = get_json
    try:
        line = photo.run(job, "Gérard Mulliez")
    finally:
        photo._get_json = original
    assert line.startswith("OK photo : Gérard Mulliez") and wiki.searches >= 1
    assert len(wiki.downloads) == 1


def test_the_search_never_takes_a_page_with_another_name(job, wiki):
    wiki.image = False
    wiki.search = [hit("Albert Einstein")]
    assert photo.run(job, "Gérard Mulliez") == photo.NONE
    assert wiki.downloads == [] and wiki.searches >= 1


def test_the_search_ranks_results_by_their_position(job, wiki):
    wiki.image = False
    wiki.search = [hit("Gérard Mulliez junior", 3, "Junior.jpg"), hit("Gérard Mulliez", 1, "Pere.jpg")]
    seen = []
    original = wiki.get_json

    def get_json(url):
        if "commons.wikimedia.org" in url:
            seen.append(url)
        return original(url)

    photo._get_json = get_json
    try:
        photo.run(job, "Gérard Mulliez")
    finally:
        photo._get_json = original
    assert "Pere.jpg" in seen[0]


def test_a_network_hiccup_is_retried_before_giving_up(job, wiki, monkeypatch):
    original = wiki.get_json
    calls = {"n": 0}

    def flaky(url):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise OSError("délai dépassé")
        return original(url)

    monkeypatch.setattr(photo, "_get_json", flaky)
    assert photo.run(job, "Ada Lovelace").startswith("OK photo : Ada Lovelace")


def test_command_line(monkeypatch):
    assert cli.parse(["photo", "job1", "Ada", "Lovelace"]) == ("photo", "job1", None, {"name": "Ada Lovelace"})
    with pytest.raises(cli.UsageError):
        cli.parse(["photo", "job1"])


def test_command_line_for_the_manual_photo(monkeypatch):
    assert cli.parse(["photo-manuel", "job1", "Jeanne Martin", "portrait.jpg", "Collection personnelle"]) == (
        "photo-manuel", "job1", None, {"name": "Jeanne Martin", "file": "portrait.jpg", "source": "Collection personnelle"})
    with pytest.raises(cli.UsageError):
        cli.parse(["photo-manuel", "job1", "Jeanne Martin", "portrait.jpg"])


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
    common.save_json(job_with_fixtures / "photo-marie-curie.json", {"person": "Marie Curie", "extension": "jpg"})
    (job_with_fixtures / "photo-marie-curie.jpg").write_bytes(b"x")
    plan["parts"][0]["scenes"].append(person_scene(plan["parts"][0]["scenes"][0]["src"], photo=True, name="Marie Curie"))
    common.save_json(job_with_fixtures / "plan.json", plan)
    assert not [e for e in plan_check.check_plan(job_with_fixtures) if "photo" in e]
    plan["parts"][0]["scenes"].pop()
    (job_with_fixtures / "photo-marie-curie.json").unlink()
    (job_with_fixtures / "photo-marie-curie.jpg").unlink()
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
    staged = [{"person": "Hermann Ebbinghaus", "image": "photo.jpg"}, {"person": "Autre Personne", "image": "photo-autre.png"}]
    assert timeline._with_photo(shared["seg_01"], staged)["props"]["photo"] == "photo.jpg"
    assert "photo" not in timeline._with_photo(shared["seg_01"], [])["props"]
    assert "photo" not in timeline._with_photo(shared["seg_01"], [staged[1]])["props"]
    assert timeline._with_photo({**shared["seg_04"], "props": {"name": "Autre Personne", "photo": True}}, staged)["props"]["photo"] == "photo-autre.png"
    assert timeline._with_photo(shared["seg_03"], staged) is shared["seg_03"]


def test_the_photos_are_copied_next_to_the_part_audio(job, tmp_path):
    out = tmp_path / "part"
    out.mkdir()
    assert timeline._stage_photo(job, out) == []
    common.save_json(job / "photo.json", {"person": "A B", "extension": "png"})
    (job / "photo.png").write_bytes(b"png")
    common.save_json(job / "photo-c-d.json", {"person": "C D", "extension": "jpg"})
    (job / "photo-c-d.jpg").write_bytes(b"jpg")
    (out / "photo-vieux.jpg").write_bytes(b"old")
    staged = timeline._stage_photo(job, out)
    assert sorted(p["image"] for p in staged) == ["photo-c-d.jpg", "photo.png"]
    assert (out / "photo.png").read_bytes() == b"png" and (out / "photo-c-d.jpg").read_bytes() == b"jpg"
    assert not (out / "photo-vieux.jpg").exists()


def artwork_scene(src, **props):
    return {"type": "artwork", "say": "La nuit étoilée est peinte en 1889 par Vincent van Gogh.",
            "props": {"title": "La nuit étoilée", "artist": "Vincent van Gogh", **props}, "items": [{"el": "title", "on": "étoilée"}], "src": src}


def store(job, person, kind=None, image=None):
    slug = person.lower().replace(" ", "-")
    image = image or f"photo-{slug}.jpg"
    data = {"person": person, "extension": "jpg"}
    if kind:
        data["kind"] = kind
    common.save_json(job / f"photo-{slug}.json", data)
    (job / image).write_bytes(b"x")


def test_an_artwork_page_is_accepted_and_stored_as_an_artwork(job, wiki):
    wiki.kind_id = "Q3305213"
    wiki.title = "La nuit étoilée"
    assert photo.run(job, "La nuit étoilée").startswith("OK photo : La nuit étoilée")
    stored = photo.all_stored(job)
    assert [(p["person"], p["kind"]) for p in stored] == [("La nuit étoilée", "artwork")]


def test_a_person_page_is_stored_as_a_person(job, wiki):
    photo.run(job, "Ada Lovelace")
    assert photo.all_stored(job)[0]["kind"] == "person"


def test_a_page_that_is_neither_a_person_nor_an_artwork_is_ignored(job, wiki):
    wiki.human = False
    assert photo.run(job, "Ada Lovelace") == photo.NONE


def test_of_kind_keeps_old_photos_as_people():
    photos = [{"person": "A", "image": "a.jpg"}, {"person": "B", "kind": "artwork", "image": "b.jpg"}, {"person": "C", "kind": "person", "image": "c.jpg"}]
    assert [p["person"] for p in photo.of_kind(photos, "person")] == ["A", "C"]
    assert [p["person"] for p in photo.of_kind(photos, "artwork")] == ["B"]


def test_an_artwork_with_the_name_of_its_painter_never_takes_the_photo_of_the_person():
    staged = [
        {"person": "Vincent van Gogh", "image": "photo-vincent-van-gogh.jpg", "kind": "person"},
        {"person": "Autoportrait de Vincent van Gogh", "image": "photo-autoportrait.jpg", "kind": "artwork"},
    ]
    card = person_scene("0:10", photo=True, name="Vincent van Gogh")
    card["props"]["name"] = "Vincent van Gogh"
    assert timeline._with_photo(card, staged)["props"]["photo"] == "photo-vincent-van-gogh.jpg"
    art = artwork_scene("0:20", title="Autoportrait de Vincent van Gogh")
    assert timeline._with_photo(art, staged)["props"]["image"] == "photo-autoportrait.jpg"


def test_an_artwork_scene_without_a_stored_image_is_refused_by_check(job_with_fixtures):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["parts"][0]["scenes"].append(artwork_scene(plan["parts"][0]["scenes"][0]["src"]))
    common.save_json(job_with_fixtures / "plan.json", plan)
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("l'image libre de droits d'une œuvre" in e for e in errors)
    store(job_with_fixtures, "Vincent van Gogh")
    errors = plan_check.check_plan(job_with_fixtures)
    assert any("l'image libre de droits d'une œuvre" in e for e in errors)
    store(job_with_fixtures, "La nuit étoilée", kind="artwork")
    assert not [e for e in plan_check.check_plan(job_with_fixtures) if "œuvre" in e or "image" in e]


def test_a_person_card_ignores_a_stored_artwork_in_check(job_with_fixtures):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["parts"][0]["scenes"].append(person_scene(plan["parts"][0]["scenes"][0]["src"], photo=True))
    common.save_json(job_with_fixtures / "plan.json", plan)
    store(job_with_fixtures, "Hermann Ebbinghaus portrait", kind="artwork")
    assert any("« photo » demande une photo libre" in e for e in plan_check.check_plan(job_with_fixtures))


def test_the_cover_never_shows_an_artwork_as_the_face_of_the_person(job):
    store(job, "Hermann Ebbinghaus portrait", kind="artwork")
    store(job, "Hermann Ebbinghaus")
    part = {"scenes": [person_scene("0:10", photo=True)]}
    assert render.cover_photo(job, part) == "photo-hermann-ebbinghaus.jpg"
    (job / "photo-hermann-ebbinghaus.json").unlink()
    assert render.cover_photo(job, part) is None
