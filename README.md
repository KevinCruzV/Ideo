# Ideo

Plugin Claude Code qui transforme une vidéo YouTube en vidéo verticale courte (1080x1920) qui l'explique : voix off, formes en papier découpé, sous-titres karaoké, et les vraies voix de la source sur les citations.

Une seule vidéo par défaut (45 s à 5 min). Plusieurs parties seulement si le contenu dépasse 5 minutes.

## Installation

Sur un Mac Apple Silicon, clone le dépôt dans `~/Desktop/ideo`, puis :

```sh
claude --plugin-dir ~/Desktop/ideo
```

Dans la session, lance `/ideo:setup`. Il vérifie et installe ffmpeg, Python, les dépendances, Remotion et le modèle de transcription, puis lance les tests.

## Utilisation

Donne une URL YouTube ("fais un short de https://youtu.be/...") ou lance `/ideo:ideo <url>`. Claude prépare la transcription, écrit le plan, te donne le chemin de `plan.md` à relire, puis rend la vidéo après ton accord. Pour aller plus loin sur un point : "approfondis ce point".

Conseil : lance la session avec le modèle le moins cher (`/model haiku`), Sonnet si le résultat ne suffit pas.

## Où sont les fichiers

Tout est dans `jobs/<id de la vidéo>/` :

- `plan.json` : le plan (tu peux modifier `hook` et `say` à la main, puis redemander le rendu)
- `plan.md` : le plan lisible, à relire avant le rendu
- `out/video.mp4` (ou `out/partie-01.mp4`, ...) : la vidéo
- `out/sources.md` : les liens minutés vers les passages de la source
- `out/description.txt` : la description à publier
- `logs/progress.log` : l'avancement (`tail -f` pour suivre)

## Coût

Claude lit la transcription compacte une fois et écrit le plan une fois. Le téléchargement, la transcription, la voix, le montage et le rendu tournent en local et ne consomment aucun crédit.
