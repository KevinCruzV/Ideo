# Supports variés et matière par vidéo : plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** chaque scène pose son contenu sur un support choisi par le code (ticket, journal, post-it, sans feuille, matière de la vidéo), et chaque vidéo a une matière choisie dans le plan.

**Architecture:** le plan gagne un champ `paper` validé par `check` et recopié dans la timeline. Le rendu calcule une fois la liste des supports (`supportsFor`) à partir des segments et de la matière, puis `Sheet` dessine le support demandé. Les scènes ne changent pas.

**Tech Stack:** Python 3 (pytest), Remotion + React + TypeScript (vitest, tsc), pnpm.

**Spec:** `docs/superpowers/specs/2026-11-26-da-supports-design.md`

## Global Constraints

- Travailler dans une copie de travail git séparée (`git worktree`) tant qu'un rendu tourne dans `~/Desktop/ideo`. Relier `render/node_modules` du dossier principal par un lien symbolique (le supprimer avant de commiter) ; le test Python de rendu réel se lance seulement dans le dossier principal.
- Valeurs de `paper` : `creme` (défaut), `kraft`, `journal`, `millimetre`, `album`.
- Aucun commentaire dans le code, aucun tiret cadratin, aucun nom de chaîne. Messages de commit sans mention de Claude.
- pnpm pour le rendu (`command pnpm`).
- Ne lancer que les tests touchés par chaque tâche (demande de Kevin) ; la suite complète une seule fois à la fin.

## Review Focus

- Plan sans `paper` : rendu identique à aujourd'hui (feuille crème), aucune erreur de `check`.
- `paper` inconnu (`"carton"`) : erreur `check` lisible qui liste les valeurs permises.
- Ambiance sombre (`mood: dark`) sans `paper` : matière `journal`, tons sombres, texte lisible.
- Deux scènes de suite au même support spécial (deux `stamp`) : la seconde prend la matière.
- Compteur sans unité ou en `%` : pas de ticket, matière de la vidéo.

---

### Task 1: Champ `paper` dans le plan, `check` et la timeline

**Files:**
- Modify: `ideo/plan_check.py` (à côté de `_check_mood`)
- Modify: `ideo/timeline.py:326` (à côté de `mood`)
- Modify: `skills/ideo/references/plan-guide.md` (paragraphe « Humeur », section 5)
- Test: `tests/test_plan_check.py`, `tests/test_timeline.py`

**Interfaces:**
- Produces: `plan_check.PAPERS = ("creme", "kraft", "journal", "millimetre", "album")` ; la timeline porte `"paper": <valeur>` seulement quand le plan l'indique.

- [ ] **Step 1: tests qui échouent**
  - `test_paper_inconnu_est_refuse` : un plan avec `"paper": "carton"` donne une erreur contenant `« paper »` et `kraft`.
  - `test_paper_valide_est_accepte` : `"paper": "kraft"` ne donne aucune erreur sur `paper`.
  - `test_paper_passe_dans_la_timeline` (dans `tests/test_timeline.py`, sur `job_with_offsets`) : absent par défaut ; `"journal"` dans le plan donne `tl["paper"] == "journal"`.
- [ ] **Step 2:** `.venv/bin/python -m pytest -q tests/test_plan_check.py tests/test_timeline.py -k paper` → FAIL.
- [ ] **Step 3:** `_check_paper(plan, errors)` appelée près de `_check_mood` ; message : `Plan : « paper » doit valoir creme, kraft, journal, millimetre ou album, ou être absent.` ; dans `build_timeline`, `if plan.get("paper") in plan_check.PAPERS: timeline["paper"] = plan["paper"]`.
- [ ] **Step 4:** guide, une ligne après « Humeur » : `Matière : ajoute "paper" au premier niveau du plan : "kraft" (argent, économie), "journal" (histoire, politique, fait divers, horreur), "millimetre" (science, santé), "album" (biographie, histoire d'une personne). Sinon n'écris rien.` Plus une ligne collages en section 5 : `Dès qu'une personne connue ou une marque est citée, lance ideo photo et montre-la (person-card avec photo ou artwork).`
- [ ] **Step 5:** même commande → PASS ; puis `pytest -q tests/test_guide.py` (vérifie le guide).
- [ ] **Step 6:** commit `Matière par vidéo : champ paper dans le plan et la timeline`.

### Task 2: Choix automatique du support (`supportsFor`)

**Files:**
- Create: `render/src/paper/supports.ts`
- Test: `render/src/paper/supports.test.ts`
- Modify: `render/src/types.ts` (`paper?: string` dans `Timeline`)

**Interfaces:**
- Produces:
  - `type Paper = "creme" | "kraft" | "journal" | "millimetre" | "album"`
  - `type Support = Paper | "ticket" | "clipping" | "postit" | "none"`
  - `paperOf(value: unknown, dark: boolean): Paper` : valeur inconnue → `creme` ; `dark` sans valeur → `journal`.
  - `supportsFor(segments: Segment[], paper: Paper): Support[]` : un support par segment (hook et outro inclus).

- [ ] **Step 1: tests qui échouent** (`supports.test.ts`)
  - counter `unit: "€"` → `ticket` ; `unit: "cts"` → `ticket` ; `unit: "%"` → matière.
  - shape-diagram `unit: "€"` → `ticket`.
  - quote et timeline → `clipping`.
  - key-title → `postit`, sauf s'il est le premier segment de type `scene` → matière.
  - stamp et mascot → `none`.
  - hook, outro et les autres types → matière.
  - deux stamp de suite → `none` puis matière ; deux quote de suite → `clipping` puis matière.
  - `paperOf("carton", false) === "creme"`, `paperOf(undefined, true) === "journal"`, `paperOf("kraft", true) === "kraft"`.
- [ ] **Step 2:** `command pnpm vitest run src/paper/supports.test.ts` → FAIL.
- [ ] **Step 3:** implémenter dans `supports.ts` ; la règle « jamais deux fois de suite » compare au support du segment précédent.
- [ ] **Step 4:** même commande → PASS ; `command pnpm tsc --noEmit` → 0.
- [ ] **Step 5:** commit `Choix automatique du support de chaque scène`.

### Task 3: Dessin des supports et branchement

**Files:**
- Modify: `render/src/paper/Sheet.tsx` (prop `support: Support`, `dark: boolean`)
- Modify: `render/src/scenes/SceneFrame.tsx` (prop `support`, transmise à `Sheet`)
- Modify: `render/src/Short.tsx` (calcule `supportsFor(timeline.segments, paperOf(timeline.paper, timeline.mood === "dark"))`, passe `support={supports[i]}`)
- Modify: `render/src/theme.ts` (couleurs des matières)
- Test: `render/src/paper/supports.test.ts` (contraste), images de test

**Interfaces:**
- Consumes: `Support`, `Paper`, `supportsFor`, `paperOf` (Task 2).
- Produces: `PAPER_COLORS: Record<Support, { fill: string; ink: string }>` exporté de `theme.ts`, pour clair et sombre.

- [ ] **Step 1: test qui échoue** : `test le texte encre reste lisible sur chaque support` : pour chaque support sauf `none`, contraste (`fill` / `ink`) ≥ 4,5 en clair et en sombre (reprendre `ratio` de `theme.test.ts`).
- [ ] **Step 2:** vitest du fichier → FAIL.
- [ ] **Step 3:** couleurs : `creme` #fbf6ea, `kraft` #c9a37a, `journal` #e6e2d8 avec colonnes de faux texte gris clair, `millimetre` #f7f8f2 avec quadrillage bleu pâle, `album` #efe3c4 ; `ticket` blanc #fefdf9, plus étroit (largeur 70 % centrée), bords haut et bas en dents régulières, sans scotch ; `clipping` = papier journal à bords droits découpés, une colonne de texte gris clair ; `postit` jaune #f7d65a carré, coin bas droit corné, sans scotch (sombre : gris #b9b4a8 avec une punaise) ; `none` = rien. Tons sombres : assombrir chaque `fill` comme `GROUNDS.dark`.
- [ ] **Step 4:** brancher `Short.tsx` → `SceneFrame` → `Sheet`.
- [ ] **Step 5:** vitest du fichier + `tsc --noEmit` → PASS.
- [ ] **Step 6:** images de test : `render/fixtures/all-scenes.json` avec `paper` = `creme`, `kraft`, `journal`, `millimetre`, `album`, et une fois avec `mood: dark` (`node scripts/stills.mjs <fixture> <dossier> --frames …` sur une image par type de support). Regarder chaque image : texte lisible, rien hors zone sûre, pas de deux supports identiques collés. Corriger avant de continuer.
- [ ] **Step 7:** commit `Supports papier variés : ticket, journal, post-it, sans feuille, matières`.

### Task 4: Album et photos en polaroïd

**Files:**
- Modify: la carte photo de `person-card` et `render/src/scenes/Artwork.tsx` (cadre polaroïd quand la matière est `album`)
- Test: images de test sur `render/fixtures/persons.json` ou un job réel avec photo

**Interfaces:**
- Consumes: `paperOf` (Task 2) via un contexte `PaperContext` fourni dans `Short.tsx`.

- [ ] **Step 1:** test vitest du helper `photoFrame(paper: Paper): "polaroid" | "plain"` → `album` donne `polaroid`, le reste `plain` ; FAIL puis implémenter, PASS.
- [ ] **Step 2:** cadre polaroïd : bord blanc épais en bas, 4 coins photo noirs triangulaires, légère rotation.
- [ ] **Step 3:** image de test d'une person-card avec photo en `album` ; regarder.
- [ ] **Step 4:** commit `Album : photos en polaroïd`.

### Task 5: Vérification finale

- [ ] Suite complète une fois : `.venv/bin/python -m pytest -q`, `command pnpm vitest run`, `command pnpm tsc --noEmit` (dans le dossier principal, après fusion de la copie de travail).
- [ ] Planche d'images comparant `creme` / `kraft` / `journal` / `album` sur 5 scènes, montrée à Kevin.
- [ ] Mettre à jour `docs/direction-artistique/README.md` (une section courte « Supports et matières »).
- [ ] Pousser sur la PR 37.
