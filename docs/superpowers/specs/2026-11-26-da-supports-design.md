# Supports variés et matière par vidéo

## Pourquoi

La direction artistique « papier découpé » plaît, mais chaque scène pose le contenu sur la même feuille crème scotchée. Sur 3 minutes et 40 scènes, ça devient répétitif. On veut varier le support sans perdre le style, sans coût de tokens en plus pour le plan.

## Objectifs

- Le support de chaque scène change selon son contenu, choisi par le code.
- Chaque vidéo a une matière de fond choisie par le modèle, en un seul champ.
- Plus de collages photo quand la source cite une personne connue ou une marque.

## Hors champ

- Pas de nouveau type de scène.
- Pas de choix de support scène par scène dans le plan.
- Pas de changement pour la cover.

## Approches considérées

- **Code automatique + matière par vidéo** (choisie par Kevin) : gratuit en tokens, cohérent ; parfois moins pertinent qu'un choix fait à la main.
- Choix du support par le modèle dans le plan : plus juste, mais plus de tokens et plus d'erreurs possibles. Écartée.

## Conception

**Matière par vidéo** : champ `"paper"` au premier niveau du plan. Valeurs :

| Matière | Pour quoi |
|---|---|
| `creme` (défaut) | Tout le reste |
| `kraft` | Argent, économie |
| `journal` | Histoire, politique, fait divers, horreur |
| `millimetre` | Science, santé |
| `album` | Biographie, histoire d'une personne |

`check` refuse une valeur inconnue. Le guide donne la règle en une ligne. En ambiance sombre (`"mood": "dark"`), `journal` par défaut et tons sombres.

**Supports automatiques** (dans le rendu, d'après le type de scène et ses props) :
- Ticket de caisse (blanc, étroit, bords dentelés) : `counter` ou `shape-diagram` dont l'unité est `€` ou `cts`.
- Coupure de journal (papier gris, fausses colonnes de texte) : `quote` et `timeline`.
- Post-it jaune au coin corné : `key-title`, sauf la première scène. En ambiance sombre : note épinglée grise.
- Sans feuille, posé sur la couleur : `stamp` (la mascotte garde une feuille : sa bulle se fondrait dans le fond).
- Ailleurs : la matière de la vidéo.
- Jamais deux fois de suite le même support spécial : la seconde scène prend la matière.

**Album** : papier jauni ; les photos (`person-card` avec photo, `artwork`) en polaroïd avec coins photo.

**Collages** : règle dans le guide : dès qu'une personne connue ou une marque est citée, lancer `ideo photo` et l'utiliser (`person-card` avec photo ou `artwork`).

## Contraintes

- Texte lisible sur chaque support (contraste vérifié par test).
- Rien ne déborde de la zone sûre TikTok.
- Pas de commentaires dans le code, pas de tiret cadratin.

## Laissé au constructeur

- Le dessin exact de chaque support (dents du ticket, colonnes du journal, coin du post-it), vérifié sur images de test.
- La taille du ticket selon le contenu.
