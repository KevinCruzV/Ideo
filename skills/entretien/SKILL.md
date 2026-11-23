---
name: entretien
description: Entretien du skill ideo. Corrige les défauts accumulés, ajoute les dessins qui ont manqué, range les leçons, et vérifie que tout marche. À utiliser quand l'utilisateur dit "entretien ideo", "améliore ideo", "corrige le skill ideo", ou quand le skill ideo affiche "Entretien à lancer".
model: sonnet
---

# Entretien d'ideo

Ce travail modifie le code du projet `~/Desktop/ideo`. Il demande un modèle capable : Sonnet au minimum. Si tu es le modèle le moins cher (Haiku), ne fais rien toi-même : lance un sous-agent Sonnet avec ce fichier comme consigne (voir le skill ideo, étape 8), ou dis à l'utilisateur de taper `/model sonnet` puis de relancer.

Règles pour tout l'entretien :
- Tu ne travailles que dans `~/Desktop/ideo`. Tu ne touches jamais à `voix/`, `config.json`, `jobs/`, ni à un autre dossier du disque.
- Tu ne pousses jamais sur GitHub (`git push` interdit). Tu ne fais jamais `git commit --amend`, `git reset --hard`, `git stash` ni `git clean`.
- Aucun commentaire dans le code. Aucun tiret cadratin. Aucun nom de chaîne YouTube, de créateur ou de projet tiers, nulle part.
- pnpm uniquement, appelé `command pnpm`. Messages de commit courts, sans aucune mention de Claude ni de co-auteur.
- Chaque correction a d'abord un test qui échoue, puis le code.
- Budget : au plus 6 défauts et 8 dessins par entretien, les plus fréquents d'abord. Le reste attend le prochain.

## Étapes

1. Prépare :
   `cd ~/Desktop/ideo && git status --short && git branch --show-current && .venv/bin/python -m ideo entretien`
   Si `git status` montre des fichiers modifiés que tu n'as pas faits, arrête-toi et lance l'étape 10 avec la raison "le dépôt a des changements en cours". Sinon lis `entretien.md` (une fois).
2. Crée une branche de travail : `git switch -c entretien/<AAAA-MM-JJ>`. Note le nom de la branche de départ.
3. Vérifie le point de départ : `.venv/bin/python -m pytest -q` puis `cd render && command pnpm vitest run && command pnpm tsc --noEmit`. Si quelque chose échoue déjà, ta première tâche est de le réparer.
4. Dessins manquants (rubrique du même nom, triée par nombre de demandes) : pour chaque dessin retenu,
   - choisis un nom anglais court en minuscules, absent de la liste ;
   - dessine-le dans `render/src/pictos/library.ts`, dans le style des dessins existants : aplats des couleurs de la palette, formes simples reconnaissables à 200 px, pas de contour fin, pas de dégradé ;
   - ajoute le nom à `PICTOS` dans `ideo/scene_schema.py` et à la liste des valeurs de `picto` dans `skills/ideo/references/plan-guide.md` (un test vérifie que les trois listes sont identiques) ;
   - rends la planche des dessins (`render/scripts/stills.mjs`, fixture des pictos) et REGARDE-la : chaque nouveau dessin doit être reconnaissable sans son nom. Sinon redessine-le.
   - coche l'entrée dans `retours.md` (`- [x]`).
5. Défauts (rubriques "Défauts signalés" et "Défauts détectés") : pour chacun, trouve la cause dans le code, écris le test qui la montre, corrige, coche l'entrée. Si le défaut est visuel, rends des images fixes de la scène concernée avant et après, et regarde-les. Un défaut que tu ne sais pas reproduire reste non coché, avec une ligne en dessous qui dit ce que tu as essayé.
6. Leçons (`skills/ideo/references/lecons.md`) : fusionne les doublons signalés dans `entretien.md`. Une leçon présente depuis plus de 5 vidéos et toujours utile passe dans `plan-guide.md`, à l'endroit du guide qui traite ce sujet, puis disparaît de `lecons.md`. Une leçon qui contredit le guide : garde la leçon et corrige le guide. Le guide ne doit pas grossir de plus de 150 mots par entretien : resserre ailleurs si besoin.
7. Vérifie tout : `.venv/bin/python -m pytest -q`, puis `cd render && command pnpm vitest run && command pnpm tsc --noEmit`. Si un job récent existe dans `jobs/`, relance aussi `.venv/bin/python -m ideo check <job>` pour voir que le plan passe toujours. Committe ton travail sur la branche d'entretien.
8. Relecture par Opus, une seule fois. Si tu peux lancer un sous-agent (outil Agent), lance-le avec `model: "opus"` et cette consigne : "Lis ~/Desktop/ideo/skills/entretien/relecture.md et fais la relecture qu'il décrit. Branche de départ : <branche de départ>. Branche d'entretien : entretien/<date>." Attends sa réponse et ajoute-la à ton résumé. Si tu ne peux pas lancer de sous-agent, ne fais rien ici : celui qui t'a lancé fera la relecture.
9. Fusion :
   - Tout est vert : committe par petits lots (`git add` des fichiers que tu as modifiés, jamais `git add -A`), reviens sur la branche de départ, `git merge --no-ff entretien/<date> -m "entretien du <date>"`, puis
     `.venv/bin/python -m ideo entretien --fait '<résumé en une phrase : N défauts corrigés, M dessins ajoutés>'`
   - Quelque chose est rouge et tu n'arrives pas à le réparer : ne fusionne rien. Committe ton travail sur la branche d'entretien, reviens sur la branche de départ sans la modifier, et passe à l'étape 10.
10. En cas d'échec ou d'arrêt :
   `cd ~/Desktop/ideo && .venv/bin/python -m ideo entretien --echec '<raison en une phrase>'`
11. Termine par trois lignes pour l'utilisateur : ce qui a été corrigé, ce qui a été ajouté, ce qui reste. Donne aussi la branche de départ et la branche d'entretien. Rappelle que rien n'est poussé sur GitHub.
