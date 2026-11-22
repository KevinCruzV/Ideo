# Retours

Une entrée par ligne : `- [ ]` à traiter, `- [x]` traitée. Les défauts signalés viennent de `python -m ideo learn --bug`, les défauts détectés du contrôle après fabrication, les dessins manquants du champ `wishes` des plans.

## Défauts signalés

- [ ] [2026-11-21] (7i3BBkUZ6PQ) Accroche : la voix locale fait rarement monter le dernier mot comme une vraie question ; sur 80 prises, aucune n'avait à la fois un « Dis-moi » court et questionnant, une fin à la bonne vitesse et une montée finale juste (cible : montée interne de 7 à 10 demi-tons).
  - Non reproduit : limite du moteur local, qui n'est plus la voix par défaut (ElevenLabs) ; les prises mesurées ne sont pas conservées, donc pas de test qui échoue ni de seuil à corriger sans données.
- [ ] [2026-11-22] (9vgV2OuqmII) La voix ElevenLabs a ajouté un mot absent du texte (« préfèrent tout garder », scène 8) sans que le contrôle de fidélité le signale.
- [ ] [2026-11-22] (9vgV2OuqmII) La voix enchaîne sans pause la fin d’une énumération et la phrase suivante (« la grippe. Entre 1500 et 1650 », scène 7).

## Défauts détectés

- [ ] `scene-figee` (ZcOLpOS-QcY) Partie 1, scène 1 (à 2,9 s) : rien n'apparaît pendant 6,3 s. Ajoute des items ancrés sur des mots de « say » ou coupe la scène en deux.
  - Non reproduit : sur les timelines actuelles de ZcOLpOS-QcY, 7i3BBkUZ6PQ et 9vgV2OuqmII, `qc._scene_alerts` ne signale aucune scène figée (les temps forts de `timeline.beat_frames` comblent les trous de plus de 4 s) ; seules les anciennes timelines sans temps forts (essai-02, fwiEcPCXLcI) la déclenchent.
- [ ] `accroche-imparfaite` (7i3BBkUZ6PQ) Partie 1 : l'accroche reste imparfaite après 12 prises (fin traînante). Relance la voix de cette partie ou reformule l'accroche.
  - Non reproduit : l'accroche vient du moteur local, remplacé par ElevenLabs dans la vidéo finale (aucun `voice-hook.json`, aucune alerte au contrôle) ; les prises d'essai sont supprimées, donc rien à rejouer pour mesurer ni régler les seuils.

## Dessins manquants

- [x] carte du canal de Panama
  - une scène `map` avec le code pa couvre ce besoin, pas de dessin à ajouter
- [x] carte du Groenland
  - une scène `map` avec le code gl et le focus arctic couvre ce besoin, pas de dessin à ajouter
- [x] carte des routes de la soie
  - une scène `map` avec `route` entre des codes de pays couvre ce besoin, pas de dessin à ajouter
- [x] drapeau de l'Irak
  - `flag:iq` existe déjà, pas de dessin à ajouter
- [x] lit à tête relevée
- [x] dormeur sur le ventre
- [x] oreiller entre les genoux
- [x] dessin d'un ronflement
- [x] bassin qui bascule
- [x] bras engourdi
