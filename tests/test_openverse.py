import io
import urllib.error

import pytest

from ideo import cli, common, openverse, photo, plan_check, timeline

JPEG = b"\xff\xd8\xff\xe0fake"
PNG = b"\x89PNG\r\n\x1a\nfake"


def result(url, width=1200, height=800, **extra):
    return {"url": url, "width": width, "height": height, "title": "Eiffel  Tower", "creator": "Jeanne",
            "license": "by", "license_version": "2.0", "license_url": "https://creativecommons.org/licenses/by/2.0/",
            "foreign_landing_url": f"{url}/page", "source": "flickr", **extra}


class Api:
    def __init__(self, results, files):
        self.results, self.files = results, files
        self.queries, self.fetched = [], []

    def get_json(self, url):
        self.queries.append(url)
        return {"results": self.results}

    def fetch(self, url):
        self.fetched.append(url)
        data = self.files.get(url)
        if isinstance(data, Exception):
            raise data
        return data


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*a, **k):
        raise AssertionError("aucun appel réseau dans les tests")

    monkeypatch.setattr("urllib.request.urlopen", blocked)
    monkeypatch.setattr(openverse.time, "sleep", lambda seconds: None)


@pytest.fixture
def job(tmp_path):
    folder = tmp_path / "job"
    folder.mkdir()
    return folder


def install(monkeypatch, results, files):
    api = Api(results, files)
    monkeypatch.setattr(openverse, "_get_json", api.get_json)
    monkeypatch.setattr(openverse, "_fetch", api.fetch)
    return api


def http_error(code):
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(b""))


def test_kind_of_reads_the_real_file_type():
    assert openverse.kind_of(JPEG) == "jpg"
    assert openverse.kind_of(PNG) == "png"
    assert openverse.kind_of(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "webp"
    assert openverse.kind_of(b"<!doctype html>") is None


def test_large_results_come_first_in_their_original_order(monkeypatch):
    install(monkeypatch, [result("s", 400, 300), result("b1"), result("s2", 1200, 500), result("b2", 900, 700)], {})
    assert [r["url"] for r in openverse.search("eiffel tower")] == ["b1", "b2", "s", "s2"]


def test_an_image_is_stored_with_its_own_prefix_kind_and_credit(monkeypatch, job):
    install(monkeypatch, [result("https://a")], {"https://a": JPEG})
    lines = openverse.run(job, ["Eiffel   tower"])
    assert lines == ["OK image : « Eiffel tower » : Eiffel Tower (flickr). Fichier : photo-img-eiffel-tower.jpg"]
    assert (job / "photo-img-eiffel-tower.jpg").read_bytes() == JPEG
    meta = common.load_json(job / "photo-img-eiffel-tower.json")
    assert meta["kind"] == "image" and meta["person"] == "Eiffel tower" and meta["license"] == "CC BY 2.0"
    assert "Photo : Eiffel Tower, Jeanne, CC BY 2.0" in (job / "out" / "sources.md").read_text(encoding="utf-8")


def test_a_page_or_a_failed_download_is_skipped_for_the_next_result(monkeypatch, job):
    files = {"https://html": b"<html>", "https://403": http_error(403), "https://ok": PNG}
    api = install(monkeypatch, [result("https://html"), result("https://403"), result("https://ok")], files)
    assert openverse.run(job, ["oil rig"])[0].endswith("photo-img-oil-rig.png")
    assert api.fetched == ["https://html", "https://403", "https://ok"]


def test_no_usable_result_says_no_image(monkeypatch, job):
    install(monkeypatch, [result("https://html")], {"https://html": b"<html>"})
    assert openverse.run(job, ["unicorn factory"]) == ["OK image : « unicorn factory » : aucune image"]
    assert not list(job.glob("photo-img-*"))


def test_too_many_requests_stops_with_a_clear_message(monkeypatch, job):
    def limited(url):
        raise http_error(429)

    monkeypatch.setattr(openverse, "_get_json", limited)
    with pytest.raises(common.IdeoError, match="Openverse limite"):
        openverse.run(job, ["eiffel tower"])


def test_several_queries_run_in_one_command(monkeypatch, job):
    install(monkeypatch, [result("https://a")], {"https://a": JPEG})
    lines = openverse.run(job, ["eiffel tower", "oil rig"])
    assert len(lines) == 2
    assert sorted(p.name for p in job.glob("photo-img-*.jpg")) == ["photo-img-eiffel-tower.jpg", "photo-img-oil-rig.jpg"]


def test_a_person_photo_search_never_deletes_an_image_with_the_same_name(monkeypatch, job):
    install(monkeypatch, [result("https://a")], {"https://a": JPEG})
    openverse.run(job, ["napoleon"])
    monkeypatch.setattr(photo, "find", lambda name, lang: None)
    photo.run(job, "Napoleon")
    assert (job / "photo-img-napoleon.jpg").exists()


def test_stored_matches_the_exact_query_only():
    photos = [{"person": "eiffel tower night", "kind": "image", "image": "a.jpg"},
              {"person": "Eiffel Tower", "kind": "image", "image": "b.jpg"},
              {"person": "eiffel tower", "kind": "person", "image": "c.jpg"}]
    assert openverse.stored(photos, "eiffel tower")["image"] == "b.jpg"
    assert openverse.stored(photos, "eiffel") is None


def image_scene(src):
    return {"type": "image", "say": "La tour Eiffel est construite en 1889 pour l'Exposition universelle.",
            "props": {"query": "eiffel tower", "caption": "La tour Eiffel"}, "items": [{"el": "caption", "on": "construite"}], "src": src}


def test_an_image_scene_needs_its_stored_image_in_check(monkeypatch, job_with_fixtures):
    plan = common.load_json(job_with_fixtures / "plan.json")
    plan["parts"][0]["scenes"].append(image_scene(plan["parts"][0]["scenes"][0]["src"]))
    common.save_json(job_with_fixtures / "plan.json", plan)
    assert any("ideo image <job> \"eiffel tower\"" in e for e in plan_check.check_plan(job_with_fixtures))
    install(monkeypatch, [result("https://a")], {"https://a": JPEG})
    openverse.run(job_with_fixtures, ["eiffel tower"])
    assert not [e for e in plan_check.check_plan(job_with_fixtures) if "ideo image" in e]


def test_the_timeline_gives_the_scene_its_image_file():
    staged = [{"person": "eiffel tower", "kind": "image", "image": "photo-img-eiffel-tower.jpg"}]
    scene = timeline._with_photo(image_scene("0:10"), staged)
    assert scene["props"]["image"] == "photo-img-eiffel-tower.jpg"
    assert "image" not in timeline._with_photo(image_scene("0:10"), [])["props"]


def test_cli_takes_several_queries():
    assert cli.parse(["image", "job1", "eiffel tower", "oil rig"]) == ("image", "job1", None, {"queries": ["eiffel tower", "oil rig"]})
