# Retours

Une entrée par ligne : `- [ ]` à traiter, `- [x]` traitée. Les défauts signalés viennent de `python -m ideo learn --bug`, les défauts détectés du contrôle après fabrication, les dessins manquants du champ `wishes` des plans.

## Défauts signalés

- [ ] [2026-11-21] (7i3BBkUZ6PQ) Accroche : la voix locale fait rarement monter le dernier mot comme une vraie question ; sur 80 prises, aucune n'avait à la fois un « Dis-moi » court et questionnant, une fin à la bonne vitesse et une montée finale juste (cible : montée interne de 7 à 10 demi-tons).
  Entretien du 2026-11-24 : critères et nombre de prises relus dans hookvoice, la montée finale vient de la voix locale elle-même ; aucun réglage du code ne la produit sans écouter de nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 : critères relus à nouveau, rien d'autre à tenter sans écoute ; même cause que l'accroche imparfaite ci-dessous. Non corrigé.
  Entretien du 2026-11-25 (c) : trois entretiens ont relu les mêmes critères sans trouver de réglage ; la montée finale dépend de la voix locale et ne peut être jugée qu'en écoutant de nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 (d) : voice-hook.json est toujours absent du dossier de la partie, donc aucun critère raté à relire ; la montée finale dépend de la voix locale et ne se juge qu'en écoutant de nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 (e) : voice-hook.json retrouvé dans kyutai/part-01 : 12 prises, prise M validée à l'oreille, montée de 12,74 demi-tons (au-dessus de la cible 7 à 10), fin à 0,63 de la vitesse du reste (seuil 0,85), formule 0,44 s, fidélité 1,0. Rien dans le code ne produit ces deux valeurs sans écouter de nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 (f) : rien de nouveau, mêmes critères relus (prise M, montée 12,74 demi-tons), aucun réglage du code ne change la voix sans nouvelle écoute. Non corrigé.
  Entretien du 2026-11-25 (g) : rien de nouveau, la montée finale dépend de la voix locale et ne se juge qu'en écoutant de nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 (h) : cause de code trouvée, distincte des précédentes : hookvoice.failed() calculait déjà la cible de montée (RISE_TARGET) pour classer les prises entre elles (distance()) mais ne s'en servait jamais pour les refuser, donc une prise dont la montée finale sortait de 7-10 demi-tons pouvait quand même être choisie et marquée « passed ». failed() refuse maintenant explicitement une montée hors cible (code « montée hors cible »), ce qui fait remonter l'alerte accroche-imparfaite même quand la prise a été choisie automatiquement. La voix locale elle-même ne peut toujours être jugée qu'à l'oreille : non corrigé (la vidéo publiée garde sa montée imparfaite), mais le défaut sera désormais signalé au lieu d'être accepté en silence.
  Entretien du 2026-11-25 (i) : job 7i3BBkUZ6PQ toujours absent de jobs/, rien de nouveau à relire. hookvoice.failed() refuse déjà la montée hors cible depuis l'entretien (h) ; la montée elle-même reste un trait de la voix locale, jugeable seulement à l'oreille sur de nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 (j) : même constat, job toujours absent de jobs/. hookvoice.best() choisit déjà la prise la moins mauvaise par rank() (qui pénalise la distance à RISE_TARGET) parmi TAKES = 12 prises, mais rien ne garantit qu'une des 12 tombe dans la cible : c'est une limite de la voix locale elle-même, pas un réglage de code manquant. Non corrigé.
- [x] [2026-11-22] (9vgV2OuqmII) La voix ElevenLabs a ajouté un mot absent du texte (« préfèrent tout garder », scène 8) sans que le contrôle de fidélité le signale.
- [x] [2026-11-22] (9vgV2OuqmII) La voix enchaîne sans pause la fin d’une énumération et la phrase suivante (« la grippe. Entre 1500 et 1650 », scène 7).
- [x] [2026-11-22] (Wj8lKdCGpY0) Les sons de transition sont presque toujours les mêmes d’une scène à l’autre : ça devient redondant, il faut les varier.
- [x] [2026-11-22] (sSm_FQ3lsg4) Fait divers, horreur, catastrophe : la direction artistique (couleurs, fonds, dessins) doit devenir sombre, pas les couleurs gaies habituelles.
- [x] [2026-11-22] (sSm_FQ3lsg4) Biographie ou histoire : il faut voir la tête de la personne principale, en grand et ressemblante, et la revoir au fil de l’histoire.
- [ ] [2026-11-22] (sSm_FQ3lsg4) La citation utilisée est lue par le youtuber, pas par la personne citée : vérifier que la voix de l’extrait n’est pas celle du narrateur.
  Entretien du 2026-11-25 (h) : assemble.quote_bounds cadre l'extrait sur le texte cité retrouvé dans la transcription de la source, sans savoir qui parle ; aucun repère de locuteur n'existe dans le dépôt, donc pas de test qui montre la cause. Non reproduit, à traiter avec un vrai cas de job.
  Entretien du 2026-11-24 : le choix de la voix de l'extrait se juge à l'écoute et à la source, aucun contrôle automatique fiable trouvé. Non automatisé.
  Entretien du 2026-11-25 : la transcription du job ne distingue pas les voix (aucun champ de locuteur dans words.json), donc rien à comparer ; la leçon « pas de scène quote quand la phrase est lue par le présentateur » reste la seule garde. Non automatisé.
  Entretien du 2026-11-25 (c) : rien de nouveau, toujours aucune information de locuteur dans la transcription. Non automatisé.
  Entretien du 2026-11-25 (d) : words.json de tous les jobs ne contient que w, s et e par mot (aucun champ de locuteur), donc rien à comparer pour savoir qui parle. Non automatisé.
  Entretien du 2026-11-25 (e) : rien de nouveau, la transcription ne donne toujours aucun locuteur et aucune empreinte de voix n'est disponible sans écouter. Non automatisé.
  Entretien du 2026-11-25 (f) : rien de nouveau, words.json ne contient toujours aucun locuteur. Non automatisé.
  Entretien du 2026-11-25 (g) : rien de nouveau, aucun locuteur dans la transcription et aucune empreinte de voix sans écouter. Non automatisé.
  Entretien du 2026-11-25 (i) : prosody.py et fidelity.py analysent la hauteur et la fidélité du texte, mais aucun des deux ne compare l'identité de deux voix ; comparer qui parle demanderait une empreinte vocale, absente du projet. Toujours aucune information de locuteur dans words.json. Non automatisé.
  Entretien du 2026-11-25 (j) : rien de nouveau, words.json (vérifié sur jobs/5H0vaCYKZHU) ne donne toujours que w, s, e par mot. plan-guide.md décrit déjà le repère textuel à chercher (« comme l'a dit X », « sur telle antenne ») pour éviter une citation lue par le présentateur ; sans empreinte vocale, c'est la seule garde possible. Non automatisé.
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
- [x] [2026-11-25] (XBLXmwxSd-0) Quand une vidéo est coupée en parties, chaque vidéo montre les barres de progression de toutes les parties : il ne faut que la barre de la partie en cours.
- [x] [2026-11-25] (XBLXmwxSd-0) Idée : pour la biographie d’un peintre, afficher une image de l’œuvre citée, avec des images libres de droits, sur le modèle des photos de personnes.
  Entretien du 2026-11-25 (d) : nouvelle scène artwork (titre, artiste, image entière) ; ideo photo accepte maintenant le titre d'une œuvre (peinture, dessin, sculpture) et garde son image libre de droits, séparée des photos de personnes.
- [x] [2026-11-25] (XBLXmwxSd-0) Le dessin vinyl ne tourne pas : dans une scène dédiée à un disque, le disque devrait tourner sur lui-même.
  Entretien du 2026-11-25 (e) : le disque du vinyl tourne maintenant sur lui-même (un tour en 1,8 s), la pochette reste fixe ; deux reflets crème de longueurs différentes rendent la rotation visible. Les autres dessins ne bougent pas.
- [x] [2026-11-25] (XBLXmwxSd-0) Aucun extrait isolé d’une chanson citée : la source ne donne que des sons d’une seconde mêlés à la voix, donc la scène d’un disque reste muette.
  Entretien du 2026-11-25 (e) : cause trouvée, un même morceau de musique de 20 à 30 s était coupé en bouts de 1 à 5 s dès que son niveau passait un instant sous le seuil (37 repères au lieu de 20 sur ce job). La détection garde maintenant un seuil plus bas une fois le son lancé, relie les pauses d'une seconde et donne des sons jusqu'à 10 s. Une chanson jouée sous la voix du narrateur reste impossible à isoler.
- [x] [2026-11-25] (XBLXmwxSd-0) La couverture est trop chargée : le titre jaune est redit en noir par l’accroche en bas. Garder un seul gros titre, avec des bandes mêlant le jaune et le noir, sans le doublon.
  Entretien du 2026-11-25 (f) : la couverture n'a plus qu'un titre. L'accroche est coupée au premier « , » ou « : » (une virgule collée à un chiffre ne coupe pas) : la première moitié en gros titre sur bande de couleur, la seconde en plus petit sur une bande noire dessous. Sans coupure, l'accroche entière fait le titre ; sans accroche, le titre de la partie. Le titre de la partie n'est plus affiché sur la couverture, la mention « Partie 1/2 » n'apparaît que si l'accroche ne nomme pas déjà la partie. La photo (ou le dessin) est plus grande et centrée dans l'espace restant.
- [x] [2026-11-25] (5H0vaCYKZHU) La recherche de photo doit laisser un vrai temps de recherche avant de conclure qu’aucune photo n’est disponible.
  Entretien du 2026-11-25 (g) : cause trouvée, ideo photo ne tentait que le titre exact de la page (en langue de la vidéo puis en anglais) et abandonnait à la première coupure réseau. Il réessaie maintenant trois fois chaque requête (attentes de 2 et 4 s), puis, si le titre exact n'a pas de photo libre, cherche dans Wikipédia (jusqu'à 8 résultats, dans l'ordre, seulement ceux dont le titre contient tous les mots du nom demandé) et prend la première page qui a une photo libre.
- [x] [2026-11-25] (5H0vaCYKZHU) La couverture doit montrer le visage en papier découpé de la figure principale avec une direction artistique de ronds de couleurs différentes derrière, même sans photo réelle de toute la famille.
  Entretien du 2026-11-25 (i) : quand aucune photo réelle n'est trouvée, la couverture reprenait un dessin du sujet ou la mascotte générique au lieu de montrer la figure principale. render.cover_look lit maintenant l'apparence (gender, age, job, hair...) de la première person-card du plan ; la couverture dessine son buste en papier découpé (PersonBust, déjà utilisé sur les person-cards) devant le disque crème, avec deux ronds plus petits de couleurs différentes derrière lui. Vérifié avec des images fixes avant (mascotte) et après (buste reconnaissable, chapeau haut-de-forme et moustache) sur une couverture sans photo.
- [x] [2026-11-25] (5H0vaCYKZHU) Il faut pouvoir chercher et afficher le vrai logo des marques citées dans une vidéo, comme la recherche de photo pour les personnes.
  Entretien du 2026-11-25 (i) : ideo photo <job> "<marque>" ne reconnaissait que les personnes et les œuvres d'art (types Wikidata), jamais une marque. photo.py reconnaît maintenant aussi les marques et entreprises (business, company, brand, organization...) sous le code "logo" ; la scène artwork (déjà utilisée pour une œuvre d'art, title sans artist) affiche aussi l'image d'un logo stocké sous ce nom, et plan_check l'accepte.
  Relecture : l'image prise est la pageimage de la page Wikipédia, pas le logo officiel (Wikidata P154) ; pour une entreprise, ça peut être la photo d'un siège ou d'un produit plutôt que le logo. Q43229 (organisation) range aussi un parti ou une ONG comme "logo". À corriger au prochain entretien : lire P154 en priorité.
- [x] [2026-11-25] (5H0vaCYKZHU) La scène versus affiche des ronds blancs parasites qu’il faut corriger.
  Entretien du 2026-11-25 (h) : cause trouvée dans Versus.tsx, le disque crème derrière le picto était rendu même sans picto (hasVisual(s.name) faux), laissant un rond crème vide de chaque côté. Il n'est plus rendu que lorsqu'un picto existe. Vérifié avec des images fixes avant/après sur une scène versus sans picto.
- [x] [2026-11-25] (5H0vaCYKZHU) L’entretien s’arrête à cause d’un fichier non suivi sans rapport avec le skill ideo (comme .claude-plugin/marketplace.json) : il doit ignorer ce qui est hors de ses propres dossiers.
  Entretien du 2026-11-25 (h) : l'étape 1 de skills/entretien/SKILL.md ne distinguait pas les fichiers du skill ideo (ideo/, render/, skills/, tests/, docs/, musique/, racine) d'un fichier non suivi ailleurs sur le disque. Elle ignore maintenant explicitement ce qui est hors de ces dossiers avant de décider d'arrêter l'entretien.
- [x] [2026-11-25] (5H0vaCYKZHU) Il faut une commande pour ajouter manuellement une photo (fichier local + source) à une person-card, en plus de la recherche automatique.
  Entretien du 2026-11-25 (h) : nouvelle commande `ideo photo-manuel <job> "<nom>" <fichier> "<source>"` (jpg, png ou webp) qui copie le fichier local dans le job et écrit son crédit dans out/sources.md, sur le même modèle de stockage que la recherche automatique (photo.add_manual). Relecture : refuse maintenant aussi un fait divers (« mood »: "dark") comme `ideo photo`, et lit le fichier avant d'oublier l'ancienne photo pour ne pas planter quand le fichier donné est déjà celui enregistré dans le job.
- [x] [2026-11-25] (bk6QIRZjMjA) La voix ElevenLabs se coupe par endroits : un mot commence puis s’interrompt, comme un fragment coupé au montage.
  Entretien du 2026-11-25 (g) : même cause que la ligne suivante, le début de la phrase suivante lu en fin de segment ; l'audio est maintenant coupé juste après le dernier mot du texte (queue de 0,12 s, fondu de 0,02 s).
- [x] [2026-11-25] (bk6QIRZjMjA) ElevenLabs lit le début de la phrase suivante (next_text) en fin de segment, et le code garde ce mot ajouté : seg_03 « coup », seg_19 et seg_27 « tropique » (Anthropic), coupés au montage.
  Entretien du 2026-11-25 (g) : quand le texte réentendu garde des mots de trop uniquement à la fin, la voix payante coupe l'audio après le dernier mot attendu, retire ces mots des repères et recalcule la ressemblance ; un mot de trop au milieu reste signalé comme avant.
- [x] [2026-11-25] (bk6QIRZjMjA) Voix coupée surtout en fin de segment, sur le dernier mot : 1:38 « en 3 jours », 2:08 « rivaux », 2:27 « AMD en tête », 2:55 « peur », 3:31 « refuse net », 3:41 « unanimité », 3:59 « approfondie » ; et en début à 0:12 sur « 4 jours avant ».
  Entretien du 2026-11-25 (g) : cause trouvée dans le resserrage des silences : la fin d'un segment était coupée au dernier instant plus fort que -32 dB (30 ms gardés), ce qui rognait la queue douce du dernier mot ; la fin des segments de ce job tombait à -33 dB, en plein mot. Le début et la fin gardent maintenant tout ce qui dépasse -50 dB. Les voix déjà générées de ce job sont à relancer pour en profiter.
- [x] [2026-11-25] (bk6QIRZjMjA) La question finale au spectateur est lue d’un ton plat, sans montée sur le dernier mot (« Nvidia ») : elle doit sonner comme une vraie question, avec du mystère.
  Entretien du 2026-11-25 (g) : la question était lue dans le même appel que l'appel à s'abonner, donc suivie d'une autre phrase. Avec ElevenLabs elle est maintenant synthétisée seule (appel à s'abonner en next_text), puis les deux audios sont recollés et les repères décalés. Le ton réel reste à écouter sur la prochaine vidéo.
- [x] [2026-11-25] (bk6QIRZjMjA) Depuis la correction des fins de mots (seuil -50 dB), on entend la respiration de la voix ElevenLabs entre les phrases ; c’est pire qu’avant, surtout avec George en stabilité 0,30.
  Entretien du 2026-11-25 (h) : les segments .wav payés ne sont pas touchés ni regénérés. À l'assemblage, pour une voix ElevenLabs, pacing.gate_breaths coupe tout ce qui est hors des mots (repères de words.json) : avant le premier mot (garde 0,08 s), après le dernier (garde 0,15 s de queue douce), et dans les écarts de 0,25 s ou plus entre mots (garde 0,15 s après un mot, 0,08 s avant le suivant), avec des fondus de 10 ms ; la durée ne change pas, donc les repères restent justes. Une partie déjà assemblée est réassemblée une fois (marqueur breath_gate dans music.json). Un nouveau produce sur ce job ne rappelle pas ElevenLabs (test avec un service qui échoue s'il est appelé). À écouter sur la prochaine vidéo : si une inspiration reste collée à un mot, augmenter BREATH_LEAD.
- [ ] [2026-11-25] (bk6QIRZjMjA) Sur iPhone, TikTok zoome et cache les bords : le titre et @idevideos passent sous la barre d’état, la scène versus est coupée à gauche et son texte de droite passe sous les boutons TikTok ; tout doit tenir dans la zone sûre.
- [x] [2026-11-25] (5H0vaCYKZHU) Quand la person-card a une vraie photo, la couverture doit aussi avoir des ronds de couleur derrière et un cadre en papier autour de la photo, pas juste la photo seule sur fond vide.
  Entretien du 2026-11-25 (j) : le cadre en papier existait déjà (PhotoFrame), mais Cover.tsx ne dessinait les deux ronds de couleur que derrière le buste de secours (bust) ou le disque crème (picto, mascotte) : la branche photo n'avait aucun rond. Les deux mêmes ronds (showsRings) s'affichent maintenant aussi derrière la photo. Vérifié avec des images fixes avant/après sur la couverture du job (photo seule, puis photo avec ronds), et sur les couvertures bust et picto pour confirmer qu'elles n'ont pas changé.
- [ ] [2026-11-25] (5H0vaCYKZHU) Même après le correctif de showsRings dans Cover.tsx, la couverture avec une vraie photo n’affiche toujours aucun rond de couleur derrière, seulement le cadre en papier : vérifier avec une image rendue, pas juste le test.
- [ ] [2026-11-25] (vtb-jGwGrd8) L'audio se coupe bizarrement juste après la phrase qui dit « résultats décevants ».
- [ ] [2026-11-25] (vtb-jGwGrd8) L'audio se coupe bizarrement sur la phrase qui dit que les PME paieraient moins d'impôt sur les sociétés.
- [ ] [2026-11-25] (vtb-jGwGrd8) La voix ElevenLabs choisie pour cette vidéo ne plaît pas à l'utilisateur.
- [ ] [2026-11-25] (vtb-jGwGrd8) L'audio a une coupure chelou vers la phrase qui dit « 100 milliards sur 5 ans ».

## Défauts détectés

- [ ] `scene-figee` (ZcOLpOS-QcY) Partie 1, scène 1 (à 2,9 s) : rien n'apparaît pendant 6,3 s. Ajoute des items ancrés sur des mots de « say » ou coupe la scène en deux.
  Entretien du 2026-11-24 : le contrôle relancé sur la timeline actuelle de ce job (avec les temps forts) ne lève plus aucune alerte, le constat venait d'un ancien rendu. Non reproduit.
  Entretien du 2026-11-25 : qc relancé sur ce job, aucune alerte scene-figee (seule la durée de la vidéo diffère du plan). Toujours non reproduit.
  Entretien du 2026-11-25 (c) : contrôle des scènes rejoué sur la timeline et les offsets actuels de la partie 1, liste d'alertes vide. Toujours non reproduit.
  Entretien du 2026-11-25 (d) : qc relancé sur ce job, une seule alerte (durée de la vidéo 176,0 s au lieu de 185,0 s), aucune alerte scene-figee. Toujours non reproduit.
  Entretien du 2026-11-25 (e) : contrôle des scènes rejoué sans rien écrire : scène 1 de 81 à 307 images, items à 90 et 264, temps fort à 190, plus grand silence visuel 3,3 s, aucune alerte. Toujours non reproduit.
  Entretien du 2026-11-25 (f) : qc relancé sur ce job, une seule alerte (durée 176,0 s au lieu de 185,0 s), aucune alerte scene-figee. Toujours non reproduit.
  Entretien du 2026-11-25 (g) : le dossier du job n'existe plus dans jobs/, rien à rejouer ; le contrôle (écart maximal entre deux apparitions, seuil 6 s) fonctionne comme prévu sur les tests. Toujours non reproduit.
  Entretien du 2026-11-25 (h) : même constat, le dossier du job n'existe toujours pas. qc._scene_alerts (IDLE_SECONDS = 6 s) fonctionne comme prévu sur les tests ; la leçon (auto:items-groupes-debut) qui évite ce trou (ancrer le dernier item sur la dernière phrase du say, pas tous au début) existe déjà dans lecons.md. Sans le plan d'origine, rien de plus à corriger dans le code. Toujours non reproduit.
  Entretien du 2026-11-25 (i) : même constat, jobs/ ne contient toujours pas ce job. scene-figee est volontairement un code détecté seulement après fabrication (codes.CODE_ONLY, testé) : le prédire à l'écriture du plan demanderait de dupliquer l'algorithme de pose des temps forts (timeline.beat_frames) sans les vrais horodatages de la voix, donc des faux positifs ou négatifs fréquents. Pas de nouvelle cause de code trouvée. Toujours non reproduit.
  Entretien du 2026-11-25 (j) : même constat, job toujours absent de jobs/. Relu timeline.beat_frames : le repêchage (la boucle while sur les points) essaie déjà n'importe quel mot du passage, pas seulement une fin de phrase, avant d'abandonner (stuck) ; un trou de 6,3 s qui subsiste après ce repêchage suppose soit un passage sans mot aligné sur cette durée, soit un ancien rendu (pacing.tighten retire déjà les pauses de plus de 0,6 s dans la voix). Sans le plan ni la voix d'origine, rien de plus à corriger dans le code sans risquer des fausses alertes. Toujours non reproduit.
- [x] `accroche-imparfaite` (7i3BBkUZ6PQ) Partie 1 : l'accroche reste imparfaite après 12 prises (fin traînante). Relance la voix de cette partie ou reformule l'accroche.
  Entretien du 2026-11-24 : même cause que le défaut signalé sur la montée finale de la voix locale, rien à corriger dans le code sans écouter de nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 : le dossier du job n'a plus de voice-hook.json, impossible de relire les critères ratés ; rien de nouveau à tenter sans nouvelles prises. Non corrigé.
  Entretien du 2026-11-25 (c) : voice-hook.json toujours absent du dossier de la partie, même cause que la montée finale ci-dessus. Non corrigé.
  Entretien du 2026-11-25 (d) : voice-hook.json toujours absent du dossier de la partie, même cause que la montée finale ci-dessus. Non corrigé.
  Entretien du 2026-11-25 (e) : le fichier est dans kyutai/part-01 et indique « prise M validée à l'oreille » : qc ne signale plus d'accroche imparfaite quand la prise est choisie à la main (vérifié sur ce fichier, aucune alerte). La montée finale reste suivie dans le défaut signalé du 2026-11-21.
- [x] `voix-plate` (Wj8lKdCGpY0) Partie 1 : voix plate, l'accroche ou la fin est plate (seg_00_hook), score médian 2,13, les plus plats : seg_00_hook (1,78), seg_18 (1,83), seg_01 (2,00). Relance la voix de cette partie ou reformule ces phrases.
  Entretien du 2026-11-24 : scores relus (accroche 1,78 pour un seuil de 2,0, médiane 2,13) ; le seuil se juge à l'oreille et la voix de ce job se relance, pas de défaut de code trouvé. Non corrigé.
  Entretien du 2026-11-25 : seule l'accroche (1,78) était sous le seuil alors que l'accroche avait été choisie parmi 12 prises par ses propres critères (fidélité, formule, vitesse, montée, niveau) ; qc ne la signale plus comme plate quand ce choix a réussi ou a été fait à la main, la fin et les autres segments restent contrôlés.
- [x] `accroche-imparfaite` (bk6QIRZjMjA) Partie 1 : l'accroche reste imparfaite après 12 prises (fidélité, formule trop longue). Relance la voix de cette partie ou reformule l'accroche.
  Entretien du 2026-11-25 (g) : le job est maintenant en ElevenLabs et son dossier n'a plus de voice-hook.json ; le constat venait d'une voix locale précédente de la même partie. La voix payante efface désormais le voice-hook.json et les scores d'intonation laissés par une voix locale pour les segments qu'elle refait.
- [x] `voix-plate` (bk6QIRZjMjA) Partie 1 : voix plate, l'accroche ou la fin est plate (seg_00_hook), score médian 2,19, les plus plats : seg_01 (1,50), seg_25 (1,63), seg_09 (1,64). Relance la voix de cette partie ou reformule ces phrases.
  Entretien du 2026-11-25 (g) : même cause, les scores d'intonation venaient de la voix locale précédente ; qc ne les trouve plus dans ce job et ils sont maintenant effacés quand la voix payante refait un segment.
- [x] `voix-infidele` (bk6QIRZjMjA) Partie 1, segment seg_03 : la voix s'écarte du texte (ressemblance 0,76). Relance la voix de cette partie ou reformule le texte.
  Entretien du 2026-11-25 (g) : la ressemblance de 0,76 venait du mot « coup » lu en fin de segment ; il est maintenant coupé et la ressemblance recalculée sans lui.
- [ ] `voix-infidele` (bk6QIRZjMjA) Partie 1, segment seg_01 : la voix s'écarte du texte (ressemblance 0,79). Relance la voix de cette partie ou reformule le texte.
  Entretien du 2026-11-25 (h) : fidelity.similarity gère bien les nombres écrits en chiffres ou en lettres (0,95 à 1,0 sur ce texte avec les deux transcriptions possibles) ; le 0,79 vient donc d'un vrai écart de lecture, à entendre. Sans relancer la voix payante (interdit ici), rien à corriger dans le code. Non corrigé.

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
