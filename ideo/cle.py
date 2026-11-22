import getpass
import json
import os
import sys
from pathlib import Path

from ideo import common, eleven

VAR = "ELEVENLABS_API_KEY"


def save_key(key: str, root: Path) -> Path:
    key = key.strip()
    if not key:
        raise common.IdeoError("clé vide, rien n'a été enregistré.")
    env_file = root / ".env"
    lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
    lines = [line for line in lines if not line.strip().startswith(f"{VAR}=")] + [f"{VAR}={key}"]
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(env_file, 0o600)
    config_file = root / "config.json"
    data = json.loads(config_file.read_text(encoding="utf-8") or "{}") if config_file.exists() else {}
    if not isinstance(data, dict):
        raise common.IdeoError("config.json doit contenir un objet JSON.")
    data.pop("elevenlabs_api_key", None)
    data["engine"] = "elevenlabs"
    config_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return env_file


def main() -> int:
    key = getpass.getpass("Colle ta clé ElevenLabs (elle ne s'affiche pas), puis Entrée : ")
    try:
        env_file = save_key(key, common._root())
    except (common.IdeoError, ValueError) as err:
        print(f"ERREUR : {err}")
        return 1
    print(f"Clé enregistrée dans {env_file} (ignoré par git, lisible par toi seul).")
    try:
        voices = eleven.list_voices()
    except common.IdeoError as err:
        print(f"ATTENTION : la clé est enregistrée mais ElevenLabs la refuse ou ne répond pas : {err}")
        return 1
    print(f"OK : ElevenLabs répond, {len(voices)} voix disponibles sur ton compte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
