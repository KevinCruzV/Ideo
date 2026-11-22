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

## La voix

Sur un Mac Apple Silicon, ideo utilise une voix locale, gratuite et sans internet une fois installée (environ 4,5 Go). Si elle manque, le skill le dit et l'installe tout seul pendant qu'il écrit le plan ; en cas d'échec ou sur un autre Mac, il utilise une voix en ligne. Chaque phrase produite est réécoutée automatiquement et refaite si elle ne correspond pas au texte.

Clé ElevenLabs : lance `.venv/bin/python -m ideo.cle`, colle la clé (elle ne s'affiche pas). Elle va dans `config.json`, ignoré par git, donc à refaire une fois sur chaque Mac après `git pull`. `config.example.json` montre les champs attendus.

Réglages facultatifs dans `config.json` à la racine (fichier ignoré par git) : `engine` (`kyutai` ou `edge`), `kyutai_voice`, `voices`, `rate`, `entretien_auto`, `entretien_seuil`.

## Le skill se relit, se contrôle et apprend

- Avant le rendu, `check` refuse les erreurs et signale des points à relire (année sans date à l'écran, pays cités sans drapeau, rythme haché, scène trop chargée) que le modèle corrige en un passage.
- Après le rendu, un contrôle automatique écrit `out/qc.md` (silences, scènes figées, sous-titres, volume, durée).
- Tes remarques sur une vidéo deviennent des leçons dans `skills/ideo/references/lecons.md`, relues à chaque vidéo. Une faute qui revient sur deux vidéos devient une leçon toute seule.
- Les défauts que seul du code peut corriger et les dessins qui ont manqué s'accumulent dans `retours.md`.
- Toutes les 5 vidéos environ, le skill lance lui-même `/ideo:entretien` en arrière-plan, sur un modèle plus capable : il corrige les défauts accumulés, ajoute les dessins manquants et range les leçons. Il ne garde ses changements que si tous les tests passent, et ne pousse jamais sur GitHub.

Pour récupérer les améliorations sur un autre Mac : `git pull`. Pour partager celles faites sur ce Mac : `git push` (leçons, retours et entretiens sont des fichiers du dépôt).

## Où sont les fichiers

Tout est dans `jobs/<id de la vidéo>/` :

- `plan.json` : le plan (tu peux modifier `hook` et `say` à la main, puis redemander le rendu)
- `plan.md` : le plan lisible, à relire avant le rendu
- `out/video.mp4` (ou `out/partie-01.mp4`, ...) : la vidéo
- `out/sources.md` : les liens minutés vers les passages de la source
- `out/description.txt` : la description à publier
- `logs/progress.log` : l'avancement (`tail -f` pour suivre)

## Coût

Claude lit le guide, les leçons et la transcription compacte une fois, écrit le plan une fois, puis corrige les points à relire. Le téléchargement, la transcription, la voix, le montage, le rendu et le contrôle tournent en local et ne consomment aucun crédit. L'entretien automatique, lui, consomme des crédits sur un modèle plus capable, environ une fois toutes les 5 vidéos.
