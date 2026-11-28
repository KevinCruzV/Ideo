---
name: ideo
description: Transforme une vidéo YouTube en vidéo verticale courte qui l'explique (voix off et formes en papier découpé). À utiliser quand l'utilisateur donne une URL YouTube avec "short", "vidéo courte", "explique-moi cette vidéo" ou "ideo", ou demande "approfondis ce point" après une vidéo ideo.
model: opus
---

# ideo

Ce skill tourne sur Opus, avec un abonnement limité : vise au moins 5 vidéos par jour. Fais tout toi-même, sans sous-agent. Entre l'URL et la vidéo finie, ne demande à l'utilisateur que la musique (étape 5) : ni validation du titre, de la storyline ou du plan, ni changement de modèle. Pose tes questions avec l'outil AskUserQuestion.

Économie, pour toute la tâche :
- Lis le guide (`plan-guide.md`), les leçons (`lecons.md`) et `transcript_compact.md` une seule fois chacun, chaque ligne une fois. Ne les relis jamais (seule exception : l'étape 2 de "Approfondis ce point").
- Fichiers du job lisibles : `transcript_compact.md` (étape 2) et `plan.json` (seulement si Edit refuse). Aucun autre : ni `words.json`, ni `plan.md`, ni les logs (sauf le `tail` de l'étape 6), ni avec Bash.
- N'affiche jamais la transcription ni le plan. Messages courts : une ou deux phrases entre les étapes.
- Chaque commande affiche `OK ...` ou `ERREUR ...`. Une ligne `ERREUR` (sauf pour `check`) : montre-la et arrête-toi.

## Étapes

1. Si l'URL contient `'` ou `"`, ne lance rien et demande un lien YouTube propre. Sinon, lance en arrière-plan (`run_in_background`) :
   `cd ~/Desktop/ideo && .venv/bin/python -m ideo prepare '<URL>'`
   Pendant ce temps, lis le guide puis les leçons : `<dossier de ce skill>/references/plan-guide.md` et `.../references/lecons.md`. Une leçon qui contredit le guide gagne.
2. À la fin, la ligne `OK prepare : <JOB> (...)` donne le dossier JOB. Recopie en une phrase son `Coût estimé`. Si elle dit `contenu long`, précise que tu feras une seule vidéo de 5 minutes au plus (guide, section 2). Puis lis `JOB/transcript_compact.md` comme l'indique la parenthèse après `Transcription :` : un seul Read, ou un Read par `offset` listé, dans l'ordre, avec la même `limit`.
   Personne historique connue (jamais un fait divers ni une personne privée) : lance une fois par personne `cd ~/Desktop/ideo && .venv/bin/python -m ideo photo JOB "<nom>"`. `OK photo : aucune photo libre` : garde le portrait en papier ; sinon mets `"photo": true` sur ses `person-card`, et dans une biographie présente-la une seule fois, pas une carte par acte. Œuvre d'art citée : même commande avec son titre ; scène `artwork` seulement si l'image est trouvée. Lieux, objets, événements à montrer en vrai : une seule commande pour toutes les recherches, `cd ~/Desktop/ideo && .venv/bin/python -m ideo image JOB "<recherche en anglais>" "<autre>"` (guide, section 5, Photos). Fait divers, horreur, catastrophe : `"mood": "dark"` au premier niveau du plan.
3. Écris `JOB/plan.json` en un seul Write, en suivant le guide (anti-plagiat et filtre anti-slop compris). Ne charge pas de skill antislop : ses règles sont dans le guide et `check` les vérifie.
4. Lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo check JOB` (pas en arrière-plan).
   - `ERREUR check : ...` : corrige seulement ce qui est nommé, avec Edit, puis relance. 4 lancements au plus ; si ça échoue encore, montre les lignes d'erreur et arrête-toi.
   - Texte copié (`recopie la vidéo d'origine mot pour mot`, `reprend des suites de 5 mots`) ou tics d'IA : réécris avec tes mots tous les `say`, `hook` et `question` qui ont ce défaut, pas seulement ceux nommés.
   - `RELIRE : <endroit> : <constat>` : ce ne sont pas des erreurs. Corrige-les toutes d'un coup, sauf si la correction rendait le plan faux, puis relance check. Deux passages de correction au plus, puis continue. Quand tu réécris un `say`, garde ses `items` ancrés sur des mots qui existent encore, le dernier dans la dernière phrase.
5. Ligne `OK check` : ne montre pas le plan. Fais choisir la musique à chaque vidéo, en une seule question AskUserQuestion :
   - Lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo musique --liste`. Propose 2 types adaptés au sujet (« funk groovy » léger, « cinématique » histoire ou grave, « acoustique » santé ou quotidien, « électro légère » technologie ; jamais de lofi), les morceaux de la liste qui collent et « aucune ».
   - « aucune » : `cd ~/Desktop/ideo && .venv/bin/python -m ideo musique JOB aucune`. Un morceau : `cd ~/Desktop/ideo && .venv/bin/python -m ideo musique JOB <nom>`.
   - Un type : `cd ~/Desktop/ideo && .venv/bin/python -m ideo musique-lien "<type en anglais>"`, puis demande : « Écoute <lien>, clique sur Téléchargement gratuit sur le morceau qui te plaît, puis réponds C'est bon. » (options « C'est bon » et « Aucune musique »), puis `cd ~/Desktop/ideo && .venv/bin/python -m ideo musique JOB --dernier` (ou `aucune`). En cas d'erreur, repose la question une fois.
   La musique est mixée sous la voix : ne propose pas de changer son niveau.
6. Lance en arrière-plan `cd ~/Desktop/ideo && .venv/bin/python -m ideo produce JOB` et attends la notification. Ne surveille pas le rendu. Si l'utilisateur demande où il en est : `cd ~/Desktop/ideo && .venv/bin/python -m ideo suivi JOB`, réponse en une phrase (avec le chemin du log s'il dit `probablement bloqué` ou `arrêté sans message`). Lis la fin de la sortie avec `tail -3` sur le fichier de sortie de la tâche.
   Garde-fou des crédits : une ligne `ERREUR` qui finit par `--payer` veut dire que produce voulait racheter une grande partie de la voix payante. Ne relance rien : demande avec AskUserQuestion, en recopiant le nombre de caractères, s'il veut payer (« Oui, paie » / « Non »). Seulement sur « Oui, paie » : `cd ~/Desktop/ideo && .venv/bin/python -m ideo produce JOB --payer` en arrière-plan. Jamais `--payer` de toi-même.
7. La ligne `OK produce : ...` liste des chemins séparés par ` ; ` : donne la ou les vidéos (`.mp4`), couvertures (`.png`, à choisir comme couverture sur TikTok), `sources.md` et descriptions (`.txt`). Recopie `Version : ...` en une phrase ; si elle dit `AUCUNE nouvelle vidéo`, dis-le tel quel. `Contrôle : N alerte(s)` : donne le chemin de `qc.md` et le nombre, sans corriger. `Voix : brouillon gratuit` : dis qu'il peut dire « version finale » quand la vidéo lui convient. Termine par : "Dis-moi ce qui ne va pas dans la vidéo, je le retiendrai pour les suivantes."
8. Entretien : il ne se lance jamais tout seul, car il coûte plusieurs vidéos de quota. Si la ligne `OK produce` contient `Entretien à lancer :` ou `Entretien conseillé :`, dis-le en une phrase avec sa raison, et propose à l'utilisateur de lancer "entretien ideo" quand il a du quota (par exemple une fois par semaine). Ne lance rien.

## Retours de l'utilisateur

Pour chaque remarque sur une vidéo ideo :
1. Texte, choix des idées, longueur, ton, accroche, scènes ou dessins : écris une règle générale d'une phrase, sans nommer la vidéo, et lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo learn '<règle>'`.
2. Image, mouvement, voix, son, sous-titres ou bug que le plan ne peut pas corriger : lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo learn --bug '<constat en une phrase>' JOB` et dis que c'est noté pour le prochain entretien, que l'utilisateur lance quand il veut ("entretien ideo"). Ne lance pas l'entretien toi-même.
3. Remplace toute apostrophe de la phrase par `’`. Montre la ligne `OK learn : ...`.
4. Pour refaire la vidéo : corrige `JOB/plan.json` avec Edit, puis reprends à l'étape 4.

## "Version finale"

Chaque vidéo sort d'abord en voix gratuite. Quand l'utilisateur la valide ("version finale", "passe en ElevenLabs", "valide la vidéo") :
1. Lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo finale JOB` et recopie en une phrase la voix et le nombre de caractères.
2. Reprends aux étapes 6 et 7.
Ne lance jamais `finale` de toi-même. Après `finale`, une correction du texte refait la voix payante des phrases modifiées : préviens l'utilisateur avant.

## "Approfondis ce point"

1. Si tu ne connais pas JOB, demande l'URL ou le dossier. Lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo deepen JOB` ; la ligne `OK deepen : nouveau job <NOUVEAU>` donne le nouveau dossier.
2. Si la transcription n'est plus dans la conversation, lis `NOUVEAU/transcript_compact.md` une fois (même découpage qu'à l'étape 2 ; `cd ~/Desktop/ideo && .venv/bin/python -m ideo cost NOUVEAU` si tu ne l'as plus). Relis le guide seulement s'il n'est plus dans la conversation.
3. Écris `NOUVEAU/plan.json` en un seul Write : une seule vidéo sur ce point, plus détaillée, avec une nouvelle accroche.
4. Reprends les étapes 4 à 7 avec NOUVEAU.

## Reprendre un job

Lance `cd ~/Desktop/ideo && .venv/bin/python -m ideo status JOB` et fais l'étape indiquée après `suivant :`.
