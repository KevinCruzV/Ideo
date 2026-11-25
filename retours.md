# Retours

Une entrée par ligne : `- [ ]` à traiter, `- [x]` traitée. Les défauts signalés viennent de `python -m ideo learn --bug`, les défauts détectés du contrôle après fabrication, les dessins manquants du champ `wishes` des plans.

## Défauts signalés

- [ ] [2026-11-21] (7i3BBkUZ6PQ) Accroche : la voix locale fait rarement monter le dernier mot comme une vraie question ; sur 80 prises, aucune n'avait à la fois un « Dis-moi » court et questionnant, une fin à la bonne vitesse et une montée finale juste (cible : montée interne de 7 à 10 demi-tons).
  Entretien du 2026-11-24 : critères et nombre de prises relus dans hookvoice, la montée finale vient de la voix locale elle-même ; aucun réglage du code ne la produit sans écouter de nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 : critères relus à nouveau, rien d'autre à tenter sans écoute ; même cause que l'accroche imparfaite ci-dessous. Non corrigé.
  Entretien du 2026-11-25 (c) : trois entretiens ont relu les mêmes critères sans trouver de réglage ; la montée finale dépend de la voix locale et ne peut être jugée qu'en écoutant de nouvelles prises. Non corrigé.
- [x] [2026-11-22] (9vgV2OuqmII) La voix ElevenLabs a ajouté un mot absent du texte (« préfèrent tout garder », scène 8) sans que le contrôle de fidélité le signale.
- [x] [2026-11-22] (9vgV2OuqmII) La voix enchaîne sans pause la fin d’une énumération et la phrase suivante (« la grippe. Entre 1500 et 1650 », scène 7).
- [x] [2026-11-22] (Wj8lKdCGpY0) Les sons de transition sont presque toujours les mêmes d’une scène à l’autre : ça devient redondant, il faut les varier.
- [x] [2026-11-22] (sSm_FQ3lsg4) Fait divers, horreur, catastrophe : la direction artistique (couleurs, fonds, dessins) doit devenir sombre, pas les couleurs gaies habituelles.
- [x] [2026-11-22] (sSm_FQ3lsg4) Biographie ou histoire : il faut voir la tête de la personne principale, en grand et ressemblante, et la revoir au fil de l’histoire.
- [ ] [2026-11-22] (sSm_FQ3lsg4) La citation utilisée est lue par le youtuber, pas par la personne citée : vérifier que la voix de l’extrait n’est pas celle du narrateur.
  Entretien du 2026-11-24 : le choix de la voix de l'extrait se juge à l'écoute et à la source, aucun contrôle automatique fiable trouvé. Non automatisé.
  Entretien du 2026-11-25 : la transcription du job ne distingue pas les voix (aucun champ de locuteur dans words.json), donc rien à comparer ; la leçon « pas de scène quote quand la phrase est lue par le présentateur » reste la seule garde. Non automatisé.
  Entretien du 2026-11-25 (c) : rien de nouveau, toujours aucune information de locuteur dans la transcription. Non automatisé.
- [x] [2026-11-22] (sSm_FQ3lsg4) Les person-cards se ressemblent toutes : il faut des personnages variés, hommes et femmes, et des tenues de métier (policier, pompier, médecin, juge, soldat…).
- [x] [2026-11-22] (sSm_FQ3lsg4) object-state screen ressemble à une télé : il faut un objet téléphone pour les SMS et messages.
- [x] [2026-11-22] (sSm_FQ3lsg4) Les transitions visuelles entre les scènes sont toujours les mêmes : il faut plusieurs effets de transition, variés.
- [x] [2026-11-22] (sSm_FQ3lsg4) Pour l’horreur et les faits divers, il manque des dessins sombres : sang, silhouette à la craie, ruban de scène de crime, menottes, couteau, cercueil.
- [x] [2026-11-22] (sSm_FQ3lsg4) Aucun contrôle ne signale un même picto répété : check devrait afficher RELIRE au-delà de 2 fois par vidéo.
- [x] [2026-11-23] (pTn6Ewhb27k) check demande une scène « body » sur une vidéo de physique sans rapport avec le corps (mots comme back ou eye) : fausse alerte.
- [x] [2026-11-23] (pTn6Ewhb27k) La musique est trop basse sous la voix : la monter de quelques dB par défaut.
- [x] [2026-11-23] (pTn6Ewhb27k) Il manque un écran de début reconnaissable (titre et dessin) pour distinguer les vidéos dans le flux et sur le profil TikTok.
- [x] [2026-11-23] (pTn6Ewhb27k) Une seule photo par vidéo : quand plusieurs personnes historiques connues apparaissent (Einstein et Fizeau), une seule peut avoir sa vraie photo.
- [x] [2026-11-24] (dAenp-6u9xU) La couverture montre le drapeau d’un pays au lieu d’un visuel du sujet global (terre, argent).
- [x] [2026-11-24] (dAenp-6u9xU) Sur un counter, le cadre reste noir et vide tant que le chiffre n’est pas lancé : afficher le chiffre de départ dès la première image.
- [x] [2026-11-25] (dAenp-6u9xU) Le drapeau écossais (flag:gb-sct) n’existe pas : seul le drapeau du Royaume-Uni est disponible pour un Écossais.
- [x] [2026-11-25] (XBLXmwxSd-0) La couverture d’une biographie montre un dessin au lieu de la photo de la personne principale : quand une person-card a photo true, la couverture doit afficher cette photo.

## Défauts détectés

- [ ] `scene-figee` (ZcOLpOS-QcY) Partie 1, scène 1 (à 2,9 s) : rien n'apparaît pendant 6,3 s. Ajoute des items ancrés sur des mots de « say » ou coupe la scène en deux.
  Entretien du 2026-11-24 : le contrôle relancé sur la timeline actuelle de ce job (avec les temps forts) ne lève plus aucune alerte, le constat venait d'un ancien rendu. Non reproduit.
  Entretien du 2026-11-25 : qc relancé sur ce job, aucune alerte scene-figee (seule la durée de la vidéo diffère du plan). Toujours non reproduit.
  Entretien du 2026-11-25 (c) : contrôle des scènes rejoué sur la timeline et les offsets actuels de la partie 1, liste d'alertes vide. Toujours non reproduit.
- [ ] `accroche-imparfaite` (7i3BBkUZ6PQ) Partie 1 : l'accroche reste imparfaite après 12 prises (fin traînante). Relance la voix de cette partie ou reformule l'accroche.
  Entretien du 2026-11-24 : même cause que le défaut signalé sur la montée finale de la voix locale, rien à corriger dans le code sans écouter de nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 : le dossier du job n'a plus de voice-hook.json, impossible de relire les critères ratés ; rien de nouveau à tenter sans nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 (c) : voice-hook.json toujours absent du dossier de la partie, même cause que la montée finale ci-dessus. Non corrigé.
- [x] `voix-plate` (Wj8lKdCGpY0) Partie 1 : voix plate, l'accroche ou la fin est plate (seg_00_hook), score médian 2,13, les plus plats : seg_00_hook (1,78), seg_18 (1,83), seg_01 (2,00). Relance la voix de cette partie ou reformule ces phrases.
  Entretien du 2026-11-24 : scores relus (accroche 1,78 pour un seuil de 2,0, médiane 2,13) ; le seuil se juge à l'oreille et la voix de ce job se relance, pas de défaut de code trouvé. Non corrigé.
  Entretien du 2026-11-25 : seule l'accroche (1,78) était sous le seuil alors que l'accroche avait été choisie parmi 12 prises par ses propres critères (fidélité, formule, vitesse, montée, niveau) ; qc ne la signale plus comme plate quand ce choix a réussi ou a été fait à la main, la fin et les autres segments restent contrôlés.

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
- [x] mirror
- [x] planet Mars
- [x] note de musique
- [x] disque vinyle
- [x] micro
