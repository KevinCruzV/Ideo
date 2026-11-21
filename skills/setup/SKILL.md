---
name: setup
description: Installe et vérifie ce dont ideo a besoin sur ce Mac (ffmpeg, Python, dépendances, Remotion, modèle de transcription). À utiliser quand l'utilisateur demande d'installer ideo, de préparer ce Mac pour ideo, ou quand une commande ideo dit qu'un outil est introuvable.
---

# Installation d'ideo

Le dépôt est dans `~/Desktop/ideo`. Lance chaque commande avec l'outil Bash, dans l'ordre. Si une vérification échoue, donne la correction indiquée à l'utilisateur et arrête-toi : ne lance pas les étapes suivantes.

1. Puce : `uname -m`. Attendu : `arm64`. Sinon dis : "ideo ne fonctionne que sur un Mac Apple Silicon (M1 ou plus récent)." et arrête-toi.
2. ffmpeg : `command -v ffmpeg && command -v ffprobe`. S'il manque : `brew install ffmpeg`.
3. Node et pnpm : `node --version && command pnpm --version`. S'il manque Node : `brew install node`. S'il manque pnpm : `brew install pnpm`.
4. Python 3.11 ou plus récent : `python3 -c "import sys; print(sys.version_info >= (3, 11))"`. Attendu : `True`. Sinon : `brew install python@3.13`.
5. Environnement Python, si `~/Desktop/ideo/.venv` n'existe pas : `cd ~/Desktop/ideo && python3 -m venv .venv`
6. Dépendances Python : `cd ~/Desktop/ideo && .venv/bin/python -m pip install -q -r requirements.txt`
7. Dépendances Remotion : `cd ~/Desktop/ideo && command pnpm --dir render install`
8. Modèle de transcription (une seule fois, environ 500 Mo) : `cd ~/Desktop/ideo && HF_HUB_DISABLE_PROGRESS_BARS=1 .venv/bin/python -c "from ideo.transcribe import load_model; load_model('small'); print('OK modèle')"`
9. Autotest : `cd ~/Desktop/ideo && .venv/bin/python -m pytest -q`. Attendu : aucune ligne `failed`. Sinon montre à l'utilisateur les noms des tests en échec.

Fin : dis "ideo est prêt. Donne-moi une URL YouTube pour faire une vidéo."
