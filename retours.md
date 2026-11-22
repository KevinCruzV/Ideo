# Retours

Une entrée par ligne : `- [ ]` à traiter, `- [x]` traitée. Les défauts signalés viennent de `python -m ideo learn --bug`, les défauts détectés du contrôle après fabrication, les dessins manquants du champ `wishes` des plans.

## Défauts signalés

- [ ] [2026-11-21] (7i3BBkUZ6PQ) Accroche : la voix locale fait rarement monter le dernier mot comme une vraie question ; sur 80 prises, aucune n'avait à la fois un « Dis-moi » court et questionnant, une fin à la bonne vitesse et une montée finale juste (cible : montée interne de 7 à 10 demi-tons).
- [x] [2026-11-22] (9vgV2OuqmII) La voix ElevenLabs a ajouté un mot absent du texte (« préfèrent tout garder », scène 8) sans que le contrôle de fidélité le signale.
- [x] [2026-11-22] (9vgV2OuqmII) La voix enchaîne sans pause la fin d’une énumération et la phrase suivante (« la grippe. Entre 1500 et 1650 », scène 7).
- [x] [2026-11-22] (Wj8lKdCGpY0) Les sons de transition sont presque toujours les mêmes d’une scène à l’autre : ça devient redondant, il faut les varier.
- [x] [2026-11-22] (sSm_FQ3lsg4) Fait divers, horreur, catastrophe : la direction artistique (couleurs, fonds, dessins) doit devenir sombre, pas les couleurs gaies habituelles.
- [x] [2026-11-22] (sSm_FQ3lsg4) Biographie ou histoire : il faut voir la tête de la personne principale, en grand et ressemblante, et la revoir au fil de l’histoire.
- [ ] [2026-11-22] (sSm_FQ3lsg4) La citation utilisée est lue par le youtuber, pas par la personne citée : vérifier que la voix de l’extrait n’est pas celle du narrateur.
- [ ] [2026-11-22] (sSm_FQ3lsg4) Les person-cards se ressemblent toutes : il faut des personnages variés, hommes et femmes, et des tenues de métier (policier, pompier, médecin, juge, soldat…).
- [ ] [2026-11-22] (sSm_FQ3lsg4) object-state screen ressemble à une télé : il faut un objet téléphone pour les SMS et messages.
- [ ] [2026-11-22] (sSm_FQ3lsg4) Les transitions visuelles entre les scènes sont toujours les mêmes : il faut plusieurs effets de transition, variés.
- [ ] [2026-11-22] (sSm_FQ3lsg4) Pour l’horreur et les faits divers, il manque des dessins sombres : sang, silhouette à la craie, ruban de scène de crime, menottes, couteau, cercueil.
- [ ] [2026-11-22] (sSm_FQ3lsg4) Aucun contrôle ne signale un même picto répété : check devrait afficher RELIRE au-delà de 2 fois par vidéo.

## Défauts détectés

- [ ] `scene-figee` (ZcOLpOS-QcY) Partie 1, scène 1 (à 2,9 s) : rien n'apparaît pendant 6,3 s. Ajoute des items ancrés sur des mots de « say » ou coupe la scène en deux.
- [ ] `accroche-imparfaite` (7i3BBkUZ6PQ) Partie 1 : l'accroche reste imparfaite après 12 prises (fin traînante). Relance la voix de cette partie ou reformule l'accroche.
- [ ] `voix-plate` (Wj8lKdCGpY0) Partie 1 : voix plate, l'accroche ou la fin est plate (seg_00_hook), score médian 2,13, les plus plats : seg_00_hook (1,78), seg_18 (1,83), seg_01 (2,00). Relance la voix de cette partie ou reformule ces phrases.

## Dessins manquants

- [x] carte du canal de Panama
- [x] carte du Groenland
- [x] carte des routes de la soie
- [x] drapeau de l'Irak
- [x] lit à tête relevée
- [x] dormeur sur le ventre
- [x] oreiller entre les genoux
- [x] dessin d'un ronflement
- [x] bassin qui bascule
- [x] bras engourdi
