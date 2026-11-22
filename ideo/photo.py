import html
import json
import re
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
NONE = "OK photo : aucune photo libre"
EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
FREE = re.compile(r"^(public domain|pd\b|cc0|cc[ -]by([ -]sa)?[ -]\d(\.\d)?\b)", re.IGNORECASE)
BLOCKED = re.compile(r"\b(nc|nd|fair use|non-?free|gfdl only)\b", re.IGNORECASE)
TAGS = re.compile(r"<[^>]+>")


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


def _is_human(item: str | None) -> bool:
    if not item:
        return False
    data = _query(WIKIDATA, action="wbgetentities", ids=item, props="claims")
    claims = data.get("entities", {}).get(item, {}).get("claims", {}).get("P31", [])
    kinds = {c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id") for c in claims}
    return HUMAN in kinds


def _file_info(filename: str) -> dict | None:
    data = _query(COMMONS, action="query", titles=f"File:{filename}", prop="imageinfo",
                  iiprop="url|extmetadata|mime", iiurlwidth=str(WIDTH))
    pages = data.get("query", {}).get("pages", [])
    infos = pages[0].get("imageinfo") if pages else None
    return infos[0] if infos else None


def find(name: str, lang: str) -> dict | None:
    for code in dict.fromkeys([lang, "en"]):
        page = _page(code, name)
        if page is None or not _is_human(page.get("pageprops", {}).get("wikibase_item")):
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


def stored(job: Path) -> dict | None:
    path = Path(job) / "photo.json"
    if not path.exists():
        return None
    try:
        data = common.load_json(path)
    except (OSError, ValueError):
        return None
    image = Path(job) / f"photo.{data.get('extension', 'jpg')}"
    return data if isinstance(data, dict) and image.exists() else None


def image_path(job: Path) -> Path | None:
    data = stored(job)
    return Path(job) / f"photo.{data['extension']}" if data else None


def credit_line(job: Path) -> str | None:
    data = stored(job)
    if not data:
        return None
    link = f" ({data['license_url']})" if data.get("license_url") else ""
    return f"Photo : {data['title']}, {data['author']}, {data['license']}{link}, {data['source_url']}"


def write_credit(job: Path) -> None:
    line = credit_line(job)
    if not line:
        return
    path = Path(job) / "out" / "sources.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else ["# Sources", ""]
    lines = [entry for entry in lines if not entry.startswith("Photo : ")]
    while lines and not lines[-1].strip():
        lines.pop()
    path.write_text("\n".join(lines + ["", line, ""]), encoding="utf-8")


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
    for stale in job.glob("photo.*"):
        stale.unlink()
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
    target = job / f"photo.{found['extension']}"
    try:
        _download(found["file_url"], target)
    except OSError as err:
        target.unlink(missing_ok=True)
        raise common.IdeoError(f"le téléchargement de la photo a échoué ({err}).") from err
    common.save_json(job / "photo.json", found)
    write_credit(job)
    return f"OK photo : {found['title']}, {found['license']}, {found['author']}. Image : {target}. Crédit ajouté à {job / 'out' / 'sources.md'}"
