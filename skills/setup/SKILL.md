---
name: setup
description: Installe et vérifie ce dont ideo a besoin sur ce Mac (ffmpeg, Python, dépendances, Remotion, modèle de transcription). À utiliser quand l'utilisateur demande d'installer ideo, de préparer ce Mac pour ideo, ou quand une commande ideo dit qu'un outil est introuvable.
---

# Installation d'ideo

Le dépôt est dans `~/Desktop/ideo`. Lance chaque commande avec l'outil Bash, dans l'ordre. Si une vérification échoue, donne la correction indiquée à l'utilisateur et arrête-toi : ne lance pas les étapes suivantes.

1. Puce : `uname -m`. Attendu : `arm64`. Sinon dis : "ideo ne fonctionne que sur un Mac Apple Silicon (M1 ou plus récent)." et arrête-toi.
2. ffmpeg : `command -v ffmpeg && command -v ffprobe`. S'il manque : `brew install ffmpeg`.
3. Node et pnpm : `node --version && command pnpm --version`. S'il manque Node : `brew install node`. S'il manque pnpm : `brew install pnpm`.
4. Python 3.11 ou plus récent : `python3 -c "import sys; print(sys.version_info >= (3, 11))"`. Attendu : `True`. Sinon : `brew install python@3.13`, puis utilise `python3.13` à la place de `python3` à l'étape 5 (ne relance pas cette vérification).
5. Environnement Python, si `~/Desktop/ideo/.venv` n'existe pas : `cd ~/Desktop/ideo && python3 -m venv .venv` (ou `python3.13 -m venv .venv` après l'installation de l'étape 4).
6. Dépendances Python : `cd ~/Desktop/ideo && .venv/bin/python -m pip install -q -r requirements.txt`
7. Dépendances Remotion : `cd ~/Desktop/ideo && command pnpm --dir render install`
8. Modèle de transcription (une seule fois, environ 500 Mo) : `cd ~/Desktop/ideo && HF_HUB_DISABLE_PROGRESS_BARS=1 .venv/bin/python -c "from ideo.transcribe import load_model; load_model('small'); print('OK modèle')"`
9. Voix locale (Mac Apple Silicon seulement, facultatif mais recommandé : voix plus naturelle, gratuite, sans internet ensuite). Dis d'abord à l'utilisateur : "Je vais installer la voix locale : environ 4,5 Go à télécharger, 10 minutes environ selon ta connexion. Sans elle, ideo utilise la voix en ligne." S'il refuse, passe à l'étape suivante. Sinon : `cd ~/Desktop/ideo && .venv/bin/python -m ideo setup-voix` (lance-la en arrière-plan et attends la fin). Elle crée `.venv-voix2`, installe `moshi_mlx`, télécharge le modèle et la voix, puis vérifie en synthétisant une phrase. Elle ne refait rien si tout est déjà prêt. Si elle répond `ERREUR setup-voix`, donne le message à l'utilisateur : la voix en ligne sera utilisée, et il peut relancer plus tard.
10. Musique de fond (facultatif, ne télécharge rien). Dis à l'utilisateur : "Pour une musique de fond discrète sous la voix, mets des morceaux libres de droits (mp3, wav, m4a, ogg ou flac) dans le dossier `~/Desktop/ideo/musique/`. Si ce dossier contient un fichier `LICENCE.txt` qui cite l'auteur et la licence (par exemple « domaine public (CC0), par Nom »), le crédit est ajouté tout seul dans `sources.md`. Un morceau est choisi par vidéo, sans répéter les trois derniers. Sans morceau, ideo fait la vidéo sans musique et le dit. Réglages facultatifs dans `config.json` : `music` (true ou false), `music_dir` (autre dossier), `music_level_db` (niveau sous la voix, -23 par défaut)." Ne crée pas le dossier et ne télécharge aucun morceau toi-même.
11. Autotest : `cd ~/Desktop/ideo && .venv/bin/python -m pytest -q`. Attendu : aucune ligne `failed`. Sinon montre à l'utilisateur les noms des tests en échec.

Fin : dis "ideo est prêt. Donne-moi une URL YouTube pour faire une vidéo."
