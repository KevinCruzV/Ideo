import hashlib
import html
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from ideo import common

API = "https://{lang}.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
WIKIDATA = "https://www.wikidata.org/w/api.php"
AGENT = "ideo-video-tool/1.0"
TIMEOUT = 30
MAX_BYTES = 12 * 1024 * 1024
WIDTH = 1200
HUMAN = "Q5"
ARTWORKS = frozenset({"Q3305213", "Q93184", "Q860861", "Q838948", "Q219423", "Q18761202"})
PERSON = "person"
ARTWORK = "artwork"
NONE = "OK photo : aucune photo libre"
EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
FREE = re.compile(r"^(public domain|pd\b|cc0|cc[ -]by([ -]sa)?[ -]\d(\.\d)?\b)", re.IGNORECASE)
BLOCKED = re.compile(r"\b(nc|nd|fair use|non-?free|gfdl only)\b", re.IGNORECASE)
TAGS = re.compile(r"<[^>]+>")
PARTICLES = frozenset({"de", "du", "des", "d", "la", "le", "les", "l", "von", "van", "der", "den", "di", "da", "del", "dos", "of", "the"})


def free_license(name: str) -> bool:
    name = (name or "").strip()
    return bool(FREE.match(name)) and not BLOCKED.search(name)


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def _download(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise common.IdeoError("la photo dépasse 12 Mo : elle est ignorée.")
    dest.write_bytes(data)


def _query(base: str, **params) -> dict:
    return _get_json(f"{base}?{urllib.parse.urlencode({**params, 'format': 'json', 'formatversion': '2'})}")


def _plain(value: str) -> str:
    return " ".join(html.unescape(TAGS.sub("", value or "")).split())


def _page(lang: str, name: str) -> dict | None:
    data = _query(API.format(lang=lang), action="query", titles=name, redirects="1", prop="pageimages|pageprops",
                  piprop="name", ppprop="wikibase_item")
    pages = data.get("query", {}).get("pages", [])
    page = pages[0] if pages else None
    if not page or page.get("missing") or not page.get("pageimage"):
        return None
    return page


def _kind_of(item: str | None) -> str | None:
    if not item:
        return None
    data = _query(WIKIDATA, action="wbgetentities", ids=item, props="claims")
    claims = data.get("entities", {}).get(item, {}).get("claims", {}).get("P31", [])
    kinds = {c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id") for c in claims}
    if HUMAN in kinds:
        return PERSON
    if kinds & ARTWORKS:
        return ARTWORK
    return None


def _file_info(filename: str) -> dict | None:
    data = _query(COMMONS, action="query", titles=f"File:{filename}", prop="imageinfo",
                  iiprop="url|extmetadata|mime", iiurlwidth=str(WIDTH))
    pages = data.get("query", {}).get("pages", [])
    infos = pages[0].get("imageinfo") if pages else None
    return infos[0] if infos else None


def find(name: str, lang: str) -> dict | None:
    for code in dict.fromkeys([lang, "en"]):
        page = _page(code, name)
        kind = _kind_of(page.get("pageprops", {}).get("wikibase_item")) if page is not None else None
        if kind is None:
            continue
        info = _file_info(page["pageimage"])
        if not info:
            continue
        meta = info.get("extmetadata", {})
        license_name = _plain(meta.get("LicenseShortName", {}).get("value", ""))
        if not free_license(license_name):
            continue
        mime = info.get("mime", "")
        url = info.get("thumburl") or info.get("url")
        if mime not in EXTENSIONS or not url:
            continue
        return {
            "kind": kind,
            "person": name.strip(),
            "title": page.get("title", name),
            "author": _plain(meta.get("Artist", {}).get("value", "")) or "auteur inconnu",
            "license": license_name,
            "license_url": _plain(meta.get("LicenseUrl", {}).get("value", "")),
            "source_url": info.get("descriptionurl") or info.get("url"),
            "file_url": url,
            "extension": EXTENSIONS[mime],
        }
    return None


def _words(text: str) -> set[str]:
    plain = "".join(c for c in unicodedata.normalize("NFKD", (text or "").lower()) if not unicodedata.combining(c))
    return set(re.findall(r"\w+", plain)) - PARTICLES


def _slug(name: str) -> str:
    words = re.findall(r"[a-z0-9]+", "".join(c for c in unicodedata.normalize("NFKD", name.lower()) if not unicodedata.combining(c)))
    return "-".join(words) or hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]


def all_stored(job: Path) -> list[dict]:
    out = []
    for meta in sorted(Path(job).glob("photo*.json")):
        try:
            data = common.load_json(meta)
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        image = meta.with_suffix(f".{data.get('extension', 'jpg')}")
        if image.exists():
            out.append({**data, "image": image.name})
    return out


def of_kind(photos: list[dict], kind: str) -> list[dict]:
    return [p for p in photos if p.get("kind", PERSON) == kind]


def match(photos: list[dict], name: str) -> dict | None:
    wanted = _words(name)
    scored = sorted(((len(wanted & _words(p.get("person", ""))), i) for i, p in enumerate(photos)), reverse=True)
    if not scored or scored[0][0] == 0 or (len(scored) > 1 and scored[1][0] == scored[0][0]):
        return None
    return photos[scored[0][1]]


def credit_lines(job: Path) -> list[str]:
    lines = []
    for data in all_stored(job):
        link = f" ({data['license_url']})" if data.get("license_url") else ""
        lines.append(f"Photo : {data['title']}, {data['author']}, {data['license']}{link}, {data['source_url']}")
    return lines


def write_credit(job: Path) -> None:
    credits = credit_lines(job)
    if not credits:
        return
    path = Path(job) / "out" / "sources.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else ["# Sources", ""]
    lines = [entry for entry in lines if not entry.startswith("Photo : ")]
    while lines and not lines[-1].strip():
        lines.pop()
    path.write_text("\n".join(lines + [""] + credits + [""]), encoding="utf-8")


def _dark(job: Path) -> bool:
    plan = Path(job) / "plan.json"
    if not plan.exists():
        return False
    try:
        data = common.load_json(plan)
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and data.get("mood") == "dark"


def run(job: Path, name: str) -> str:
    job = Path(job)
    name = name.strip()
    if not name:
        raise common.IdeoError("donne le nom de la personne : ideo photo <job> \"Prénom Nom\".")
    if _dark(job):
        raise common.IdeoError("pas de photo pour un fait divers : garde le portrait en papier découpé.")
    slug = _slug(name)
    for old in all_stored(job):
        if _slug(old.get("person", "")) == slug:
            (job / old["image"]).unlink(missing_ok=True)
            (job / old["image"]).with_suffix(".json").unlink(missing_ok=True)
    lang_file = job / "lang.txt"
    lang = lang_file.read_text(encoding="utf-8").strip() if lang_file.exists() else "fr"
    try:
        found = find(name, lang or "fr")
    except OSError as err:
        raise common.IdeoError(f"Wikipédia est injoignable ({err}). Réessaie plus tard ou garde le portrait en papier.") from err
    except ValueError as err:
        raise common.IdeoError(f"réponse illisible de Wikipédia ({err}).") from err
    if not found:
        return NONE
    target = job / f"photo-{slug}.{found['extension']}"
    try:
        _download(found["file_url"], target)
    except OSError as err:
        target.unlink(missing_ok=True)
        raise common.IdeoError(f"le téléchargement de la photo a échoué ({err}).") from err
    common.save_json(target.with_suffix(".json"), found)
    write_credit(job)
    return f"OK photo : {found['title']}, {found['license']}, {found['author']}. Image : {target}. Crédit ajouté à {job / 'out' / 'sources.md'}"
