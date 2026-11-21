---
name: ideo
description: Transforme une vidéo YouTube en vidéo verticale courte qui l'explique (voix off et formes en papier découpé). À utiliser quand l'utilisateur donne une URL YouTube avec "short", "vidéo courte", "explique-moi cette vidéo" ou "ideo", ou demande "approfondis ce point" après une vidéo ideo.
---

# ideo

Conseil à donner une fois à l'utilisateur au début : cette tâche marche avec le modèle le moins cher, tape `/model haiku` (passe à Sonnet si le résultat ne suffit pas).

Règles pour toute la tâche :
- Lis le guide (`plan-guide.md`), les leçons (`lecons.md`) et `transcript_compact.md` UNE seule fois chacun : chaque ligne est lue une fois, jamais deux. Pour la transcription, c'est un seul Read, ou les Read par morceaux que donne la ligne `OK prepare` (étape 2). Ne les relis jamais. Seule exception : l'étape 2 de "Approfondis ce point".
- Fichiers du job que tu peux lire : `transcript_compact.md` (une fois, étape 2) et `plan.json` (seulement si Edit refuse, étape 4). Aucun autre : ni `words.json`, ni `plan.md`, ni les logs (sauf la commande `tail` de l'étape 6). Ne les affiche pas non plus avec Bash (`cat`, `head`).
- N'affiche jamais la transcription ni le plan dans la conversation.
- Chaque commande affiche une ligne `OK ...` ou `ERREUR ...`. Une ligne `ERREUR` (sauf pour `check`, étape 4) : montre-la à l'utilisateur et arrête-toi.

## Étapes

1. Si l'URL contient une apostrophe ou un guillemet (`'`, `"`), ne lance rien : dis à l'utilisateur que l'URL est invalide et demande un lien YouTube propre. Sinon, lance avec l'outil Bash, en arrière-plan (`run_in_background`), avec l'URL entre apostrophes simples :
   `cd ~/Desktop/ideo && .venv/bin/python -m ideo prepare '<URL>'`
   Pendant que ça tourne, lis avec l'outil Read le guide puis les leçons, dans le même dossier : `<dossier de base affiché au chargement de ce skill>/references/plan-guide.md` et `.../references/lecons.md` (normalement `/Users/<toi>/Desktop/ideo/skills/ideo/references/`). Les leçons sont des règles tirées des vidéos précédentes : applique-les comme le guide. Si une leçon contredit le guide, la leçon gagne.
2. Attends la notification de fin. La ligne `OK prepare : <JOB> (...)` donne le dossier du job, appelé JOB ci-dessous. Elle finit par `Coût estimé : ...` : recopie cette estimation à l'utilisateur en une phrase, par exemple "Coût estimé : lecture au moins ~7 400 tokens, écriture ~2 000 à 3 500 tokens. Chaque correction après `check` ajoute un peu." Si elle dit `contenu long`, ajoute que tu feras une seule vidéo de 5 minutes au plus avec les idées principales, sauf si le contenu utile dépasse nettement 5 minutes ou s'il demande plusieurs parties (règle du guide, section 2). Puis, sans attendre de réponse, lis `JOB/transcript_compact.md` avec l'outil Read, comme l'indique la parenthèse après `Transcription : <chemin>` :
   - `à lire en un seul Read` : un seul Read, sans `offset` ni `limit`.
   - `trop longue pour un seul Read` : un Read par `offset` listé, dans l'ordre, chacun avec la même `limit`, jusqu'au dernier. Exemple pour `offset 1, 107, 213, chacun avec limit 106` : Read avec offset 1 et limit 106, puis offset 107 et limit 106, puis offset 213 et limit 106. Ne saute aucun morceau et n'en relis aucun.
3. Écris `JOB/plan.json` en UN seul appel de l'outil Write, en suivant le guide.
4. Lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo check JOB` (pas en arrière-plan).
   - Lignes `ERREUR check : ...` : corrige seulement ce qu'elles nomment, avec l'outil Edit sur `JOB/plan.json`, puis relance check. Si Edit refuse parce que le fichier a changé, lis `JOB/plan.json` une fois avec Read, puis refais l'Edit.
   - Lance check 3 fois au plus de suite. Après le 3e échec, montre les lignes d'erreur à l'utilisateur et arrête-toi. Le compte repart à zéro après chaque demande de l'utilisateur.
   - Relecture : quand check réussit, il peut afficher des lignes `RELIRE : <endroit> : <constat>`. Ce ne sont pas des erreurs. Corrige chacune avec Edit sur `JOB/plan.json`, sauf si la correction rendrait le plan faux ou contraire à la source. Fais toutes les corrections, puis relance check UNE fois. S'il reste des lignes `RELIRE` après ce passage, continue sans les corriger. Ce passage ne compte pas dans les 3 lancements.
5. Ligne `OK check : ... Relecture : <chemin de plan.md>`. Elle donne le nombre de scènes et la durée estimée : dis-les à l'utilisateur. Dis-lui aussi, sans montrer le contenu :
   "Le plan est prêt : <chemin de plan.md>. Tu peux modifier `hook` et `say` dans `JOB/plan.json`, ou me demander une correction précise. Dis go pour lancer la vidéo."
   Attends sa réponse. S'il demande une correction : fais-la avec Edit sur `plan.json`, puis retourne à l'étape 4. S'il a modifié le fichier lui-même : retourne à l'étape 4.
6. Après son go, lance en arrière-plan :
   `cd ~/Desktop/ideo && .venv/bin/python -m ideo produce JOB`
   Attends la notification de fin. Si l'utilisateur demande où en est le rendu, lance `tail -n 3 JOB/logs/progress.log` et donne la réponse en une phrase.
7. La ligne `OK produce : ...` liste des chemins séparés par ` ; `. Donne-les à l'utilisateur : la ou les vidéos (`.mp4`), `sources.md` et la ou les descriptions (`.txt`). Elle finit par `Contrôle : N alerte(s)` : s'il y en a, donne à l'utilisateur le chemin de `qc.md` et le nombre d'alertes, sans les corriger toi-même. Termine par : "Dis-moi ce qui ne va pas dans la vidéo, je le retiendrai pour les suivantes."

## Retours de l'utilisateur

Quand l'utilisateur dit ce qui ne va pas (ou ce qui lui plaît) dans une vidéo ideo, le skill doit s'en souvenir. Pour chaque remarque :
1. Si elle porte sur le texte, le choix des idées, la longueur, le ton, l'accroche, le choix des scènes ou des dessins : écris-la comme une règle générale d'une phrase, valable pour toutes les vidéos, sans nommer cette vidéo. Exemple : "Trop d'événements, on ne suit pas" devient "Garde 4 ou 5 événements au plus et explique chacun en 3 scènes." Lance :
   `cd ~/Desktop/ideo && .venv/bin/python -m ideo learn '<règle>'`
2. Si elle porte sur l'image, le mouvement, la voix, le son, les sous-titres ou un bug, que le plan ne peut pas corriger : lance
   `cd ~/Desktop/ideo && .venv/bin/python -m ideo learn --bug '<constat en une phrase>' JOB`
   et dis à l'utilisateur que c'est noté pour une correction du code.
3. Remplace toute apostrophe de la phrase par `’` avant de lancer la commande. Montre à l'utilisateur la ligne `OK learn : ...`.
4. S'il veut aussi refaire cette vidéo : corrige `JOB/plan.json` avec Edit, puis reprends à l'étape 4.

## "Approfondis ce point"

Quand l'utilisateur demande d'approfondir un point d'une vidéo déjà faite :
1. Si tu ne connais pas JOB, demande à l'utilisateur l'URL ou le dossier de la vidéo. Lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo deepen JOB`. La ligne `OK deepen : nouveau job <NOUVEAU>` donne le nouveau dossier. La vidéo précédente reste intacte.
2. Seule exception à la règle de lecture unique : si la transcription n'est plus dans la conversation, lis `NOUVEAU/transcript_compact.md` une fois, chaque ligne une seule fois : un seul Read si elle tient, sinon par morceaux consécutifs avec `offset` et `limit` (même découpage qu'à l'étape 2 ; lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo cost NOUVEAU` si tu ne l'as plus). Si le guide n'est plus dans la conversation, lis-le une fois. S'ils y sont encore, ne relis rien.
3. Écris `NOUVEAU/plan.json` en un seul Write : une seule vidéo sur ce point seulement, plus détaillée, avec une nouvelle accroche qui ne reprend pas la formule de la précédente.
4. Reprends les étapes 4 à 7 avec NOUVEAU à la place de JOB.

## Reprendre un job

Si l'utilisateur revient sur un job existant, lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo status JOB` et fais l'étape que la ligne indique après `suivant :`.
