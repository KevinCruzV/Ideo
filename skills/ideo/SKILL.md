---
name: ideo
description: Transforme une vidéo YouTube en vidéo verticale courte qui l'explique (voix off et formes en papier découpé). À utiliser quand l'utilisateur donne une URL YouTube avec "short", "vidéo courte", "explique-moi cette vidéo" ou "ideo", ou demande "approfondis ce point" après une vidéo ideo.
---

# ideo

Conseil à donner une fois à l'utilisateur au début : cette tâche marche avec le modèle le moins cher, tape `/model haiku` (passe à Sonnet si le résultat ne suffit pas).

Règles pour toute la tâche :
- Lis le guide (`plan-guide.md`) et `transcript_compact.md` UNE seule fois chacun. Ne les relis jamais. Seule exception : l'étape 2 de "Approfondis ce point".
- Fichiers du job que tu peux lire : `transcript_compact.md` (une fois) et `plan.json` (seulement si Edit refuse, étape 4). Aucun autre : ni `words.json`, ni `plan.md`, ni les logs (sauf la commande `tail` de l'étape 6). Ne les affiche pas non plus avec Bash (`cat`, `head`).
- N'affiche jamais la transcription ni le plan dans la conversation.
- Chaque commande affiche une ligne `OK ...` ou `ERREUR ...`. Une ligne `ERREUR` (sauf pour `check`, étape 4) : montre-la à l'utilisateur et arrête-toi.

## Étapes

1. Lance avec l'outil Bash, en arrière-plan (`run_in_background`) :
   `cd ~/Desktop/ideo && .venv/bin/python -m ideo prepare "<URL>"`
   Pendant que ça tourne, lis le guide avec l'outil Read : `<dossier de base affiché au chargement de ce skill>/references/plan-guide.md` (normalement `/Users/<toi>/Desktop/ideo/skills/ideo/references/plan-guide.md`).
2. Attends la notification de fin. La ligne `OK prepare : <JOB> (...)` donne le dossier du job, appelé JOB ci-dessous. Lis `JOB/transcript_compact.md` avec l'outil Read.
3. Écris `JOB/plan.json` en UN seul appel de l'outil Write, en suivant le guide.
4. Lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo check JOB` (pas en arrière-plan).
   - Lignes `ERREUR check : ...` : corrige seulement ce qu'elles nomment, avec l'outil Edit sur `JOB/plan.json`, puis relance check. Si Edit refuse parce que le fichier a changé, lis `JOB/plan.json` une fois avec Read, puis refais l'Edit.
   - Lance check 3 fois au plus de suite. Après le 3e échec, montre les lignes d'erreur à l'utilisateur et arrête-toi. Le compte repart à zéro après chaque demande de l'utilisateur.
5. Ligne `OK check : ... Relecture : <chemin de plan.md>`. Dis à l'utilisateur, sans montrer le contenu :
   "Le plan est prêt : <chemin de plan.md>. Tu peux modifier `hook` et `say` dans `JOB/plan.json`, ou me demander une correction précise. Dis go pour lancer la vidéo."
   Attends sa réponse. S'il demande une correction : fais-la avec Edit sur `plan.json`, puis retourne à l'étape 4. S'il a modifié le fichier lui-même : retourne à l'étape 4.
6. Après son go, lance en arrière-plan :
   `cd ~/Desktop/ideo && .venv/bin/python -m ideo produce JOB`
   Attends la notification de fin. Si l'utilisateur demande où en est le rendu, lance `tail -n 3 JOB/logs/progress.log` et donne la réponse en une phrase.
7. La ligne `OK produce : ...` liste des chemins séparés par ` ; `. Donne-les à l'utilisateur : la ou les vidéos (`.mp4`), `sources.md` et la ou les descriptions (`.txt`). Fin.

## "Approfondis ce point"

Quand l'utilisateur demande d'approfondir un point d'une vidéo déjà faite :
1. Si tu ne connais pas JOB, demande à l'utilisateur l'URL ou le dossier de la vidéo. Lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo deepen JOB`. La ligne `OK deepen : nouveau job <NOUVEAU>` donne le nouveau dossier. La vidéo précédente reste intacte.
2. Seule exception à la règle de lecture unique : si la transcription n'est plus dans la conversation, lis `NOUVEAU/transcript_compact.md` une fois ; si le guide n'est plus dans la conversation, lis-le une fois. S'ils y sont encore, ne relis rien.
3. Écris `NOUVEAU/plan.json` en un seul Write : une seule vidéo sur ce point seulement, plus détaillée, avec une nouvelle accroche qui ne reprend pas la formule de la précédente.
4. Reprends les étapes 4 à 7 avec NOUVEAU à la place de JOB.

## Reprendre un job

Si l'utilisateur revient sur un job existant, lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo status JOB` et fais l'étape que la ligne indique après `suivant :`.
