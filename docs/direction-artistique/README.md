# Rythme et direction artistique (novembre 2026)

## 1. Ce qu'on a mesuré

Outil : `python -m ideo rythme <job | fichier vidéo> [--seuil 0.15]` (voir `ideo/rythme.py`).

Cinq vidéos TikTok de storytelling servent de référence : Petrov en pixel art, sorcières de 1600, Hushpuppi, « La tresse », Tupac. Elles sont comparées à deux vidéos Ideo finalisées (Nvidia/Anthropic, Leclerc/Aldi). Les chiffres excluent l'écran de fin TikTok.

| | Petrov | Sorcières | Hushpuppi | Tresse | Tupac | **Ideo Nvidia** | **Ideo Leclerc** |
|---|---|---|---|---|---|---|---|
| Durée | 61 s | 94 s | 201 s | 93 s | 150 s | 250 s | 173 s |
| Plans/min | 27 | 34 | 22 | 27 | ~19 (à l'œil) | **7** | **6** |
| Plan médian | 2,0 s | 1,4 s | 2,6 s | 2,2 s | ~3 s | **8,8 s** | **9,0 s** |
| Mots par plan (médiane) | 3,5 | 6 | 8 | 9 | n.d. | **25** | **28** |
| Mots/s hors pauses | 3,7 | 4,1 | 4,4 | 4,9 | 4,5 | 3,7 | 3,7 |
| Part du temps en pause | 30 % | 1 % | 29 % | 21 % | 22 % | 23 % | 16 % |
| Sous-titres | 1-2 mots | 1-2 mots | mots-clés | 1 mot | mots-clés | ~4 mots, petits | ~4 mots, petits |

Conclusions :
- **Plans :** l'écart principal est là. Les références montrent un nouveau plan toutes les 1,5 à 3 s, y compris dans les vidéos longues (Hushpuppi, 3 min 20). Ideo en montrait un toutes les 9 s.
- **Voix :** le débit d'Ideo est correct, dans le bas de la fourchette.
- **Vidéos longues :** elles gardent l'attention avec la structure annoncée au début (« quatre pistes »), un carton par chapitre environ toutes les 30 s, et une fin en suspens vers la partie suivante.
- **Silences :** de vrais silences de 2 à 4 s, sur un ou deux moments forts au plus.
- **Un plan n'est pas forcément un nouveau dessin :** même décor, autre cadrage, autre personnage ou autre accessoire.

Limites :
- **Échantillon réduit :** 5 vidéos de référence.
- **Vidéos très sombres :** la détection de coupes ffmpeg sous-compte les changements entre deux plans sombres (Tupac : 10 plans/min mesurés, environ 19 à l'œil).
- **Ponctuation :** Whisper ponctue mal un débit sans pause (Sorcières), donc la longueur des phrases n'y est pas fiable.

## 2. Ce qui a changé dans Ideo (PR #37)

**Direction artistique « papier découpé abouti »** (choisie parmi 3 maquettes de cover) :
- Fond plein cadre en version **adoucie** de la couleur de la scène (15 % de crème, `GROUNDS` dans `render/src/theme.ts`). Il change à chaque scène, et il est assombri en ambiance sombre. La version vive prenait trop de place, 45 % puis 28 % étaient trop pastel : voir `fonds-compares.jpg` (de haut en bas : 28 %, 15 %, 8 %).
- Le contenu est posé sur une feuille crème déchirée et scotchée (`render/src/paper/Sheet.tsx`). Le texte n'est jamais posé directement sur la couleur.
- Les mots-clés (accroche, titres, étiquettes) sont en Unbounded.
- Sous-titres : 1 à 2 mots (`MAX_GROUP = 2`), très gros, dans une étiquette noire, avec le mot prononcé en jaune.
- Cover : titre géant sur la feuille, suite de l'accroche dans une étiquette noire, dessin qui déborde, le tout centré dans le recadrage 3:4 de la grille du profil.
- Personnage historique ou connu : la vraie photo (`ideo photo`) reste utilisée. Dans les scènes, elle est encadrée sur la feuille (carte de personnage). Sur la cover, elle est épinglée sous le titre sans le recouvrir. Les deux cas ont été rendus avec une image de test.

**Rythme :**
- **Recadrage :** l'image se recadre net à chaque élément qui apparaît (`render/src/scenes/punch.ts`), et change au moins toutes les 2,5 s (`BEAT_GAP`).
- **Carton de chapitre :** carton plein écran avec le `kicker` au début de chaque scène `"break": true`.
- **Suspense :** `"suspense": true` donne 2 s de silence avant une révélation, deux au plus par vidéo. C'est vérifié par `check`, géré dans l'assemblage audio et exempté dans `qc`.
- **Plafond de `check` :** le « rythme haché » n'est signalé qu'au-delà de 15 scènes/min, au lieu de 9.
- **Pas plus de scènes :** le plan n'en demande pas davantage au modèle. Le changement d'image vient des recadrages automatiques, ce qui évite d'alourdir le plan et son coût.

Images : `scenes-avant.jpg`, `scenes-apres.jpg`, `covers.jpg`, `fonds-compares.jpg`.

## 3. Reste à faire

1. **Faire une vraie vidéo de bout en bout sur le Mac** (`prepare` → plan → `produce`), puis la mesurer avec `python -m ideo rythme <job>`. Rien n'a encore été vérifié sur une vraie voix : sous-titres de 1 à 2 mots, recadrages, carton de chapitre, silence de suspense. Objectif : au moins 15 plans/min.
2. **Vérifier une cover et une carte de personnage avec une vraie photo d'archive.** Le cadrage a été validé avec une image de test, pas avec une vraie photo.
3. **Carton de chapitre quand le `kicker` n'est qu'une date** (« 1991 ») : le carton affiche alors juste la date. Décider s'il faut prendre le nom de l'acte ailleurs.
4. **Si les recadrages ne suffisent pas,** demander des scènes plus courtes dans `plan-guide.md`. Le repère actuel est 6-9 s, soit 18-26 mots ; on pourrait passer à 4-6 s. Cela coûte plus de tokens au moment d'écrire le plan.
5. **Outil `rythme` sur les vidéos très sombres :** améliorer la détection de coupes, par exemple en éclaircissant l'image avant le filtre de scène.
6. **Données de test :** `render/fixtures/*.json` contiennent encore des sous-titres de 3 à 4 mots, générés avec l'ancien réglage. Les régénérer pour que les images de test reflètent le rendu réel.
7. **Rendu des images de test dans un conteneur cloud :** `render/scripts/stills.mjs` télécharge Chrome depuis remotion.media, ce qui est bloqué. Il faudrait une option pour passer `browserExecutable` (par exemple `/opt/pw-browsers/chromium_headless_shell`). Sur le Mac, rien ne change.
8. **Revoir et fusionner la PR #37.**

## 4. Environnement cloud

- **Environnement « Ideo » :** environnement cloud personnel créé pendant cette session. Il autorise Hugging Face, pour le modèle Whisper de `rythme`, et Google Drive.
- **Téléchargement du modèle Whisper :** passe par `HF_HUB_DISABLE_XET=1` ou par l'hôte `cas-server.xethub.hf.co`.
- **Maquettes des directions de cover et des scènes :** artifact privé « Ideo, directions de cover » sur claude.ai.
