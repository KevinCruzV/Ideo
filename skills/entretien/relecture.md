# Relecture d'un entretien

Tu relis, une seule fois, le travail d'un entretien du skill ideo dans `~/Desktop/ideo`. On te donne la branche de départ et la branche d'entretien.

Mêmes règles que `SKILL.md` de l'entretien : pas de `git push`, pas de `--amend`, `reset --hard`, `stash` ni `clean`, aucun commentaire dans le code, aucun tiret cadratin, aucun nom de chaîne ou de créateur, aucune mention de Claude dans les commits. Tu ne touches jamais à `voix/`, `config.json` ni `jobs/`.

1. `cd ~/Desktop/ideo && git status --short`. Si des fichiers sont modifiés, arrête-toi et réponds : « Relecture non faite : le dépôt a des changements en cours. »
2. `git switch <branche d'entretien>`, puis lis `git diff <branche de départ>...HEAD` et `skills/ideo/references/lecons.md` en entier.
3. Cherche seulement :
   - des leçons en double ou qui se contredisent : fusionne-les ;
   - des leçons vagues : réécris-les avec un exemple concret, 200 caractères au plus ;
   - des leçons qu'un contrôle de `ideo/plan_check.py` pourrait vérifier tout seul : signale-les, sans écrire le contrôle ;
   - une correction qui traite le symptôme et pas la cause, ou un test qui ne prouve pas la correction : corrige si c'est court, sinon signale ;
   - une entorse aux règles ci-dessus : corrige-la (pour un message de commit, signale-la seulement).
4. Si tu as modifié quelque chose : `.venv/bin/python -m pytest -q`, puis `cd render && command pnpm vitest run && command pnpm tsc --noEmit`. Si tout est vert, committe (`git add` des fichiers modifiés, message court « relecture de l'entretien »). Sinon annule tes changements avec `git checkout -- <fichiers>` et signale le problème.
5. Reviens sur la branche où tu étais au départ. Si l'entretien avait déjà été fusionné dans la branche de départ, refais `git merge --no-ff <branche d'entretien> -m "relecture de l'entretien"`.
6. Réponds en trois lignes au plus : ce que tu as corrigé, ce que tu signales sans l'avoir corrigé. Si tout était bon : « Relecture : RAS. »
