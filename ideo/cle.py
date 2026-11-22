import getpass
import json
import os
import sys
from pathlib import Path

from ideo import common, eleven


def save_key(key: str, path: Path) -> None:
    key = key.strip()
    if not key:
        raise common.IdeoError("clé vide, rien n'a été enregistré.")
    data = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
        if not isinstance(data, dict):
            raise common.IdeoError("config.json doit contenir un objet JSON.")
    data["elevenlabs_api_key"] = key
    data["engine"] = "elevenlabs"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def main() -> int:
    path = common._root() / "config.json"
    key = getpass.getpass("Colle ta clé ElevenLabs (elle ne s'affiche pas), puis Entrée : ")
    try:
        save_key(key, path)
    except (common.IdeoError, ValueError) as err:
        print(f"ERREUR : {err}")
        return 1
    print(f"Clé enregistrée dans {path} (fichier ignoré par git, lisible par toi seul).")
    try:
        voices = eleven.list_voices()
    except common.IdeoError as err:
        print(f"ATTENTION : la clé est enregistrée mais ElevenLabs la refuse ou ne répond pas : {err}")
        return 1
    print(f"OK : ElevenLabs répond, {len(voices)} voix disponibles sur ton compte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
