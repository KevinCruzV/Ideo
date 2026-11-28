import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ideo import common, photo

API = "https://api.openverse.org/v1/images/"
PAGE = 20
TRIES = 6
MIN_SIDE = 600
IMAGE = photo.IMAGE
PREFIX = "photo-img-"
NONE = "aucune image"
LIMITED = "Openverse limite les recherches pour l'instant : réessaie dans une minute ou fais la scène sans image."
SIGNATURES = ((b"\xff\xd8\xff", "jpg"), (b"\x89PNG\r\n\x1a\n", "png"))
LICENSE_NAMES = {"cc0": "CC0", "pdm": "domaine public"}


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": photo.AGENT})
    with urllib.request.urlopen(request, timeout=photo.TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": photo.AGENT})
    with urllib.request.urlopen(request, timeout=photo.TIMEOUT) as response:
        data = response.read(photo.MAX_BYTES + 1)
    if len(data) > photo.MAX_BYTES:
        raise ValueError("image trop lourde")
    return data


def kind_of(data: bytes) -> str | None:
    for signature, extension in SIGNATURES:
        if data.startswith(signature):
            return extension
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def search(query: str) -> list[dict]:
    url = f"{API}?{urllib.parse.urlencode({'q': query, 'page_size': PAGE})}"
    for attempt in range(1, photo.ATTEMPTS + 1):
        try:
            data = _get_json(url)
            break
        except urllib.error.HTTPError as err:
            if err.code == 429:
                raise common.IdeoError(LIMITED) from err
            if attempt == photo.ATTEMPTS:
                raise
        except OSError:
            if attempt == photo.ATTEMPTS:
                raise
        time.sleep(2 * attempt)
    results = [r for r in data.get("results", []) if isinstance(r, dict) and r.get("url")]
    big = [r for r in results if min(r.get("width") or 0, r.get("height") or 0) >= MIN_SIDE]
    return big + [r for r in results if r not in big]


def _license(result: dict) -> str:
    code = str(result.get("license") or "").lower()
    if code in LICENSE_NAMES:
        return LICENSE_NAMES[code]
    version = result.get("license_version")
    return f"CC {code.upper()} {version}".strip() if version else f"CC {code.upper()}".strip()


def slug(query: str) -> str:
    return photo._slug(query)


def stored(photos: list[dict], query: str) -> dict | None:
    wanted = slug(query)
    return next((p for p in photo.of_kind(photos, IMAGE) if slug(p.get("person", "")) == wanted), None)


def _forget(job: Path, query: str) -> None:
    old = stored(photo.all_stored(job), query)
    if old:
        (job / old["image"]).unlink(missing_ok=True)
        (job / old["image"]).with_suffix(".json").unlink(missing_ok=True)


def find(job: Path, query: str) -> str:
    query = " ".join(query.split())
    _forget(job, query)
    try:
        results = search(query)
    except (OSError, ValueError) as err:
        raise common.IdeoError(f"Openverse est injoignable ({err}). Réessaie plus tard ou fais la scène sans image.") from err
    for result in results[:TRIES]:
        try:
            data = _fetch(result["url"])
        except urllib.error.HTTPError as err:
            if err.code == 429:
                raise common.IdeoError(LIMITED) from err
            continue
        except (OSError, ValueError):
            continue
        extension = kind_of(data)
        if extension is None:
            continue
        target = job / f"{PREFIX}{slug(query)}.{extension}"
        target.write_bytes(data)
        meta = {
            "kind": IMAGE,
            "person": query,
            "title": " ".join(str(result.get("title") or query).split()),
            "author": str(result.get("creator") or "auteur inconnu"),
            "license": _license(result),
            "license_url": str(result.get("license_url") or ""),
            "source_url": str(result.get("foreign_landing_url") or result["url"]),
            "extension": extension,
        }
        common.save_json(target.with_suffix(".json"), meta)
        return f"OK image : « {query} » : {meta['title']} ({result.get('source', '?')}). Fichier : {target.name}"
    return f"OK image : « {query} » : {NONE}"


def run(job: Path, queries: list[str]) -> list[str]:
    job = Path(job)
    queries = [q for q in (" ".join(q.split()) for q in queries) if q]
    if not queries:
        raise common.IdeoError("donne au moins une recherche en anglais : ideo image <job> \"eiffel tower\" \"oil rig\".")
    lines = [find(job, query) for query in queries]
    photo.write_credit(job)
    return lines
