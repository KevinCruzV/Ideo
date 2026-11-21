# ideo : conception

Date : 2026-11-21
Repo : `github.com/KevinCruzV/ideo` (à créer, compte perso)
Dossier local : `~/Desktop/ideo`

Légende : **[Kevin]** = décidé par Kevin. **[Proposition]** = choix de Claude, à corriger.

## 1. Intention

Kevin veut apprendre à partir de vidéos YouTube éducatives longues, sans les regarder en entier. L'outil prend
l'URL d'une vidéo et en fait une **série de shorts verticaux** (Partie 1, 2, 3...) qui réexpliquent les idées
principales, avec une voix off (sa propre voix clonée) et un montage animé stylé. **[Kevin]**

Au départ, c'est un projet perso pour apprendre. **[Kevin]** Kevin demande maintenant une watermark et un appel à
s'abonner en fin de vidéo : les shorts sont donc susceptibles d'être publiés (à la main). **[Interprétation de
Claude, à confirmer]**

## 2. Objectifs, non-objectifs, anti-objectifs

**Objectifs**
- N'importe quelle URL YouTube éducative en entrée. **[Kevin]**
- Montage "ludique" = visuel stylé avec dessins et animations, pas de mécanique de jeu. **[Kevin]**
- Voix off avec la voix de Kevin, clonée en local, gratuit. **[Kevin]**
- Chaque affirmation de la voix off reste rattachée au passage de la vidéo source qui la justifie (minutage),
  pour que Kevin puisse vérifier. **[Proposition]**, pour limiter le risque d'apprendre une erreur de résumé.

**Non-objectifs**
- Pas de quiz, pas de questions, pas de gamification. **[Kevin]**
- Pas de publication automatique (TikTok, YouTube). **[Proposition]**
- Pas d'images de la vidéo source dans le short : tout est refait (voix off + visuels). **[Kevin]**, déduit des
  exemples choisis.

**Anti-objectifs** (ce qui ferait échouer le projet même si "ça marche")
- Un rendu qui "fait IA" : Kevin a demandé explicitement d'appliquer les règles anti-slop. **[Kevin]**
- Un résumé qui déforme le contenu de la vidéo source.
- Une copie conforme du look d'une chaîne existante.

## 3. Contraintes

- Machine : Mac (Apple Silicon supposé, à confirmer), tout tourne en local sauf Claude.
- Pas de coût récurrent au-delà de l'abonnement Claude de Kevin. **[Kevin]** (préférence pour le gratuit / local)
- Gestionnaire de paquets Node : pnpm. Python pour l'audio et la transcription.
- L'échantillon de voix de Kevin n'est **jamais** commité (gitignore). **[Proposition]**
- Licences : Remotion est gratuit pour un particulier (licence Remotion, à revérifier au moment de l'installation).
  Le modèle de voix doit gérer le français.

## 4. Approches envisagées

1. **Plugin Claude Code + Remotion** **[Kevin, retenue]**. Le projet est un plugin Claude
   Code. Claude fait le travail de compréhension (découpage en parties, écriture des textes, choix des scènes) dans
   la conversation, donc sans coût d'API et avec une relecture possible avant le rendu. Python récupère, transcrit
   et génère la voix. Remotion (React) rend la vidéo, calée sur le minutage de chaque mot.
2. Script autonome + API Claude + Remotion. Une commande, aucune conversation, mais coût d'API à l'usage et moins
   de contrôle sur le texte. Écartée.
3. Tout en Python (ffmpeg + sous-titres ASS + images fixes). Démarrage rapide,
   mais les dessins animés et le surligneur mot à mot y sont pénibles, le rendu ferait bricolé. Écartée.

## 5. Ce qui est décidé

### 5.1 Pipeline

Une "job" par URL, dans `jobs/<slug>-<hash>/`.

1. **fetch** (Python, yt-dlp) : métadonnées (titre, chaîne, chapitres YouTube si présents) + **audio seul**. La
   vidéo n'est pas téléchargée puisqu'aucune image source n'apparaît dans le short. **[Proposition]**
2. **transcribe** (Python, faster-whisper) : transcription avec minutage par mot -> `transcript.json`.
3. **plan** (Claude, dans un skill) : Claude lit la transcription et écrit `plan.json` : la liste des parties,
   et pour chaque partie le texte de la voix off découpé en scènes. Chaque scène porte son type visuel, son
   contenu, et les minutages source qui la justifient.
4. **relecture** : Claude montre à Kevin les parties et leurs textes. Kevin valide ou corrige avant toute
   génération de voix. **[Proposition]**
5. **voice** (Python) : génère la voix off de chaque partie avec le clone de la voix de Kevin -> `voice.wav`,
   puis la retranscrit avec faster-whisper pour obtenir le minutage de chaque mot prononcé.
6. **render** (Remotion) : rend chaque partie en MP4 1080x1920, 30 fps, scènes calées sur les mots.
7. **sortie** : `jobs/<id>/out/partie-01.mp4`, ... + `sources.md` (pour chaque partie, les liens YouTube
   minutés vers les passages d'origine).

### 5.2 Voix off

- Clone **local et gratuit** de la voix de Kevin. **[Kevin]**
- Modèle : Chatterbox Multilingual (open source, licence MIT, gère le français) en premier choix, F5-TTS en
  repli. **[Proposition]** Le builder valide la qualité en français avant de figer le choix.
- Échantillon : Kevin enregistre une fois 30 à 60 s de sa voix, stocké hors git (`voice/reference.wav`).
- Un skill `setup-voix` guide l'enregistrement et fait un essai d'écoute.

### 5.3 Ce que font les références (observé)

Plusieurs vidéos de deux chaînes de référence ont été regardées image par image le 2026-11-21.
Les deux chaînes sont visiblement faites à partir de gabarits : on retrouve les mêmes zones, les mêmes
composants et le même rythme d'une vidéo à l'autre.

**Trois zones fixes**
- En haut : une étiquette de contexte (chapitre "PARTIE 2 / LES GAGES", ou autocollant "L'ENFANCE", "EN 4E").
  Sur l'une, un compteur en haut à droite ("cadeaux : 0 -> 1").
- Au centre : un seul visuel principal (décor, objet, carte, illustration).
- En bas : sous-titres karaoké de 2 à 4 mots, mot prononcé en couleur ou dans un bloc d'accent, mots suivants
  atténués. Sur l'autre, le personnage principal reste en bas de l'écran pendant toute la vidéo.

**Construction progressive calée sur la voix**
- Une scène dure 5 à 10 s. Les éléments y apparaissent un par un, chacun sur un mot de la voix off. Il y a
  peu de coupes : on enrichit l'écran plutôt que d'en changer.
- Un micro-événement toutes les 2 à 3 s (un élément qui arrive, un mot qui se surligne, un état qui change).

**L'objet central réagit à ce qui est dit**
- La télé se fissure ("CRAC !"), Pronote affiche "erreur 503", le compteur passe de 0 à 1, les cartes
  s'empilent, un tampon s'écrase en biais ("PURGE OBLIGATOIRE"), des bulles s'empilent au-dessus des personnages.

**Vocabulaire de composants observé**
carte de personne (avatar rond, nom, fonction) ; étiquettes de fait ("12 ans", "2018", "Gagner, c'est
normal") ; liste de cartes empilées ; compteur ; frise chronologique (2016 -> 2026) ; grille de pictogrammes en
tuiles ; tampon en biais ; gros nombre ou année ; avatars mystère "?" ; carte citation avec mots surlignés ;
autocollant onomatopée ("CRAC !", "HAHA") ; bulles de dialogue ; étiquettes de nom au-dessus des personnages ;
confettis ; fond en rayons de soleil pour la fin ; écran (télé, ordinateur) qui sert d'afficheur.

**Spécificités**
- Référence A : décors plats en aplats (pièce avec mur et sol de couleur, fenêtre, canapé, télé), un décor détaillé
  qui reste tout au long de la vidéo ou une couleur de pièce par chapitre, personnages simples et ronds,
  couleurs chaudes et saturées.
- Référence B : pictogrammes et illustrations en aplats dans des panneaux, titres très gras condensés avec un
  mot dans un bloc d'accent, barre de progression par segments en bas.

### 5.4 Ce que reprend ideo

**Reprise des mécaniques, pas des assets** **[Proposition]** : les trois zones, la construction progressive
calée sur les mots, l'objet central qui réagit, et le vocabulaire de composants ci-dessus, adaptés à
l'apprentissage. On ne reprend ni la mascotte ni les décors d'une chaîne existante tels quels (anti-objectif
"pas de copie d'une chaîne"). La mascotte d'ideo est conçue pour ideo et validée par Kevin.

**Composants de départ (Remotion)** **[Proposition]** :

| Composant | Rôle dans une explication |
|---|---|
| `etiquette-chapitre` + `progression` | où on en est dans la série et dans la partie |
| `titre-cle` | la phrase-clé, un mot dans le bloc d'accent |
| `carte-personne` | qui dit ou a fait quoi |
| `etiquettes-faits` | chiffres, dates, définitions courtes qui s'ajoutent |
| `liste-empilee` | étapes ou arguments qui s'accumulent |
| `compteur` | "3 raisons", "2e erreur" qui s'incrémente |
| `frise` | chronologie, avant/après |
| `grille-pictos` | catégories, familles d'éléments |
| `tampon` | conclusion forte, idée reçue démentie |
| `citation` | phrase exacte de la source (+ extrait audio, section 10) |
| `decor-objet` | un décor plat avec un objet qui change d'état (écran, tableau, machine...) |
| `mascotte` | la question naïve, la réaction (bulle, autocollant) |
| `sous-titres` | karaoké 2 à 4 mots, toujours présent |

**Ancrage sur les mots, pas sur le temps** **[Proposition]**, pour l'économie de crédits : dans `plan.json`,
Claude rattache chaque apparition à un mot ou une expression du texte qu'il écrit ("apparaît sur
'verrouille'"). Aucun minutage dans le plan. Une étape locale convertit ces ancres en temps après la génération
de la voix et sa retranscription.

**Pictogrammes et décors** : une bibliothèque dessinée une fois pendant le développement, dans le style validé.
Claude choisit dans cette bibliothèque par nom.

### 5.4 bis Identité visuelle

**[Kevin]** ideo a **sa propre direction artistique**. Les références servent à comprendre ce qui marche
(mécanique, rythme, lisibilité), pas à reprendre leur look : ni leurs fonds, ni leurs
décors, ni leur mascotte. Une première série de maquettes trop proche de leurs DA a été rejetée.

**Direction retenue [Kevin] : la géométrie en papier découpé, fond ivoire** (fusion des maquettes D1 "papier
découpé" et D3 "géométrie" du 2026-11-21).

- **Formes** : chaque idée s'explique avec des formes simples (ronds, carrés, bandes, flèches) dont la taille,
  le nombre et la position portent le sens (exemple : un rond qui rétrécit jour après jour pour l'oubli).
- **Matière** : chaque forme est découpée dans du papier coloré, posée avec une ombre courte et nette, avec de
  légères rotations. Les textes à l'écran sont des bandes de papier collées de travers.
- **Mouvement** : les éléments arrivent de façon un peu saccadée, façon stop-motion (animation à environ
  12 images/s dans une vidéo à 30 images/s), toujours calés sur un mot de la voix.
- **Fond** : ivoire uni (#f4efe4 sur la maquette), choisi pour la lisibilité sur téléphone. Pas de dégradé,
  pas de halo, pas de grille.
- **Couleurs** : rouge tomate (#e2462c), jaune moutarde (#f5bf2a), bleu cobalt (#2747c9), papier crème
  (#fbf6ea) pour les bandes de texte, encre presque noire (#1f1a14). Une couleur porte l'accent par écran.
- **Typographie** : Bricolage Grotesque (grotesque aux formes un peu irrégulières, qui va avec le "fait main")
  pour les textes et sous-titres ; Unbounded pour la watermark "Ideo". À confirmer à l'usage.
- **Sous-titres** : karaoké 2 à 4 mots, le mot prononcé sur une bande de papier de couleur.
- **Watermark** : "Ideo" sur une petite étiquette de papier en haut à droite.
- **Mascotte** : en papier découpé dans ce style, conçue pour ideo, 2 ou 3 propositions à valider par Kevin.

Maquette de référence : `docs/mockups/style-fusion.html` (fond ivoire).

### 5.5 Forme du repo

**[Proposition]**

```
ideo/
  .claude-plugin/plugin.json
  skills/
    setup/            installe ffmpeg, Python deps, pnpm deps, vérifie la voix
    setup-voix/       enregistrement de l'échantillon + essai
    ideo/ le skill principal : URL -> plan -> relecture -> voix -> rendu
  scripts/            Python : fetch, transcribe, voice, common
  render/             projet Remotion (pnpm) : compositions + composants de scènes
  docs/superpowers/specs/
  jobs/               (gitignore)
  voice/              (gitignore)
```

## 6. Laissé au builder

- Le format exact de `plan.json` (schéma), tant qu'il couvre parties, scènes, texte, minutages source.
- La façon de passer `plan.json` + minutage des mots à Remotion (props, fichier).
- Le choix entre faster-whisper et une variante plus rapide sur Mac (mlx-whisper) pour la transcription.
- Le détail des animations, dans le cadre MOTION 2 et du motif surligneur.
- Les tests : au minimum, un rendu de bout en bout sur une vidéo courte de référence.

## 7. Choix de Claude après relecture

Tous **[Proposition]**, à corriger par Kevin.

- **Exécution** : le plugin se lance depuis le clone local `~/Desktop/ideo`. `jobs/`, `voice/` et le projet
  Remotion vivent dans ce dossier. Pas d'installation via marketplace en v1.
- **Anti-slop** : le référentiel est le plugin `antislop` (v3.2.25). Il s'applique une fois, à la conception des
  composants et du guide de style. Le guide de style SVG (traits, couleurs, interdits) est figé dans le repo
  (`render/STYLE.md`) : le plugin n'est pas une dépendance à l'exécution. Échelle des réglages : 1 calme,
  2 équilibré, 3 audacieux.
- **Voix, critère d'acceptation** : c'est Kevin qui juge, à l'oreille, pendant `setup-voix` (phrase d'essai en
  français). La voix est une couche interchangeable derrière une seule fonction `synthétiser(texte) -> wav`.
  Si ni Chatterbox ni F5-TTS ne conviennent, repli temporaire sur une voix de synthèse non clonée (edge-tts),
  le projet n'est pas bloqué. Le pipeline se construit et se teste d'abord avec ce repli, l'échantillon de
  Kevin n'est donc pas requis au début.
- **Jalons** : (1) pipeline de bout en bout avec placeholders visuels et voix de repli ; (2) maquette du style
  (palette, typo, 2 ou 3 propositions de mascotte dessinées en SVG par Claude) validée par Kevin, jalon
  bloquant avant de considérer la v1 terminée ; (3) clone de voix.
- **Relecture avant rendu** : elle couvre les textes. Les SVG de `schema` et `exemple` ne sont pas montrés un
  par un ; Kevin les voit dans le rendu et peut demander de refaire une scène.

## 8. Langue

**[Kevin]** Le short est dans la langue de la vidéo source : vidéo en anglais, short en anglais (voix off,
sous-titres, textes à l'écran).

Conséquences **[Proposition]** :
- La langue est détectée à la transcription et écrite dans `plan.json`. Tout le reste la suit.
- Les cartes `citation` montrent la phrase d'origine telle quelle, sans traduction.
- Le clone de voix doit parler plusieurs langues à partir du même échantillon français : c'est une raison de
  plus de préférer un modèle multilingue. La qualité est à juger par Kevin langue par langue (au minimum
  français et anglais).
- Les libellés fixes de l'interface vidéo ("Partie 2") sont traduits dans la langue du short.

## 9. Durée et couverture

**[Kevin]** Une vidéo longue donne seulement ses idées principales, pas une couverture complète.

**[Kevin, mis à jour le 2026-11-21]** Un short peut durer plus de 90 s : de 2 à 5 minutes selon le contenu, ou
moins. Découper en parties n'est pas obligatoire : on l'évite quand le contenu tient dans une seule vidéo.

Détail **[Proposition]** :
- Par défaut, **une seule vidéo** par source, de 45 s à 5 min (300 s), à la longueur que le contenu demande.
- On découpe en parties seulement si le contenu utile dépasse 5 min, avec 8 parties au maximum, chacune de
  45 s à 5 min et compréhensible seule.
- Avec une seule vidéo : pas de "Partie 1" à l'écran (seulement le titre), et la fin dit "Abonne-toi pour la
  prochaine vidéo" au lieu d'annoncer une partie suivante.
- Kevin peut demander après coup d'approfondir un point, ce qui produit une vidéo supplémentaire à partir de
  la même transcription, sans tout refaire.
- Les étapes voix et rendu se relancent vidéo par vidéo.

## 10. Bande-son

**[Kevin]** Pas de sons venus d'ailleurs : quand la vidéo source contient des bruitages ou des personnes qui
parlent, on les reprend dans le short, et ils sont extraits de la vidéo elle-même.

Détail **[Proposition]** :
- La bande-son d'un short = la voix off de Kevin + des extraits audio de la source. Aucune musique ni
  bruitage externe.
- **Extraits de parole** : dans une scène `citation`, on entend la vraie voix de la personne (extrait découpé
  grâce au minutage par mot), pendant que la phrase s'affiche. La voix off s'arrête pendant l'extrait.
  Quelques secondes par extrait, pour que le short reste une réexplication et pas un remontage.
- **Bruitages de la source** : Claude ne peut pas écouter l'audio. Le repérage se fait donc par indices :
  passages sans paroles mais avec du son (trou dans la transcription + volume élevé), et mentions dans la
  transcription. C'est du "au mieux" : fiable pour les paroles, approximatif pour les bruitages. À la
  relecture, Kevin voit la liste des extraits retenus avec leur minutage et peut en retirer ou en ajouter.
- Mixage : niveaux normalisés, extraits fondus à
  l'entrée et à la sortie.
- L'étape **fetch** garde donc l'audio complet de la source dans la job.
- Les **images** de la source ne sont toujours pas utilisées : seul le son est repris. (Interprétation de
  Claude, à confirmer par Kevin.)

## 11. Économie de crédits Claude

**[Kevin]** Le plugin doit consommer le moins de crédits possible : il servira aussi sur un autre PC avec un
abonnement Claude Pro (20 EUR), tout en gardant une très bonne qualité vidéo.

Principe **[Proposition]** : Claude ne fait qu'une chose, écrire `plan.json`. Tout le reste est du code qui
tourne en local et ne coûte aucun crédit.

- **Une seule lecture de la transcription.** Un script prépare une version compacte pour Claude : phrases
  regroupées par paragraphe avec un seul minutage par paragraphe, sans le minutage mot à mot (qui reste dans
  un fichier que Claude ne lit jamais). Ordre de grandeur estimé, à mesurer : 30 000 tokens pour 2 h de vidéo.
- **Une seule écriture.** Claude écrit `plan.json` en une fois : parties, textes de voix off, gabarit et
  paramètres de chaque scène. Pas de SVG généré à chaque vidéo : c'est ce qui coûterait le plus en sortie, et
  c'est aussi la première cause d'un rendu inégal.
- **Relecture dans un fichier, pas dans la conversation.** Le plan est aussi écrit en `plan.md` lisible. Kevin
  le corrige lui-même dans le fichier, ou demande une correction ciblée. Claude ne réaffiche pas tout.
- **Scripts silencieux.** Chaque script n'affiche qu'une ligne de résultat. Les journaux vont dans des fichiers.
  Les étapes longues (transcription, voix, rendu) tournent en arrière-plan.
- **Reprise sans relecture.** L'état d'une job est sur disque. Une nouvelle session reprend à l'étape suivante
  sans relire la transcription.
- **Skill court.** Le `SKILL.md` principal tient en une page. Le guide d'écriture et la liste des gabarits sont
  dans un seul fichier de référence, lu une fois à l'étape plan.
- **Validation par code.** Un script vérifie `plan.json` (schéma, durées, minutages existants) et renvoie
  seulement les erreurs, pour éviter que Claude se relise.
- **Modèle.** L'étape plan doit donner un bon résultat avec le modèle par défaut de l'abonnement Pro. Le builder
  le vérifie sur une vidéo de référence et mesure la consommation réelle.
- La qualité vidéo ne dépend pas des crédits : elle vient des gabarits, du guide de style et du rendu Remotion,
  conçus une fois pendant le développement.

## 12. Portabilité

**[Kevin]** Le plugin sera utilisé sur un deuxième ordinateur, un Mac lui aussi. Seul macOS est visé.

**[Proposition]** Puce Apple Silicon supposée sur les deux Mac. Le skill `setup` le vérifie et prévient si la
machine est trop juste pour le clone de voix (dans ce cas, repli sur la voix de synthèse).

- L'échantillon de voix n'est pas dans git : Kevin le copie à la main sur l'autre machine.
- Le skill `setup` doit installer et vérifier toutes les dépendances sur chaque système visé.

## 13. Watermark et fin de vidéo

**[Kevin]** Chaque short porte toujours une watermark, et se termine par un appel à s'abonner pour en apprendre
plus.

Détail **[Proposition]** :
- Watermark : discrète, toujours au même endroit, hors des trois zones (pour ne masquer ni le visuel ni les
  sous-titres), présente du début à la fin. Texte : **"Ideo"** **[Kevin]**. Traitement typographique décidé avec
  la maquette d'identité.
- Fin de vidéo : une scène de clôture de 2 à 3 s, dite par la voix off, qui fait partie de la série plutôt
  qu'une formule générique. Exemple : "Abonne-toi pour la partie 3 : <titre de la partie suivante>". Sur la
  dernière partie : "Abonne-toi pour la prochaine série". Le texte suit la langue du short (section 8).
- Si les shorts sont publiés : la description générée crédite la vidéo source (titre, chaîne, lien). Reprendre des extraits audio de la source (section 10) dans une vidéo publiée pose
  une question de droits que Kevin assume ; ideo ne publie rien lui-même.

## 14. Accroche d'ouverture

**[Kevin]** Chaque short commence par une accroche, dans un style "dis-moi pourquoi...". **[Kevin]** Même format à
chaque fois (même animation, même place, même rythme : c'est la signature), mais la phrase est adaptée au sujet.
"Dis-moi pourquoi..." est la formule par défaut quand elle colle.

Détail **[Proposition]** :
- Les 2 à 3 premières secondes : une question ou une affirmation qui donne envie de connaître la réponse,
  affichée en gros (composant `accroche`) et dite par la voix off. Le reste de la partie y répond.
- Familles de formules : "Dis-moi pourquoi... ?", "Pourquoi... ?", "Tu sais ce qui se passe quand... ?",
  "Et si... ?", "Personne ne t'explique que...". Claude choisit celle qui colle au contenu et ne réutilise pas la
  même formule deux parties de suite : une série où chaque short commence pareil fait "généré".
- L'accroche doit être vraie et tenue par la partie : pas de promesse que le contenu ne tient pas, pas de
  chiffre inventé (R-17, R-36).
- Elle suit la langue du short (section 8) : en anglais, "Tell me why...", "Why...?", etc.
- Ordre d'une partie : accroche -> explication -> fin "abonne-toi pour la partie suivante" (section 13).

## 15. Crédit des extraits cités

**[Kevin]** Quand un extrait audio est cité, on crédite celui qu'on entend (une personne, un journal, une
émission), pas la chaîne YouTube qui a publié la vidéo. Aucun nom de chaîne ou de créateur n'apparaît dans ce
que produit ideo.

Détail **[Proposition]** :
- Le crédit affiché sur une citation (`speaker`) vient de ce que dit la transcription autour de l'extrait. Si
  elle ne dit pas qui parle, pas de crédit : jamais un crédit inventé, jamais la chaîne.
- Le vérificateur refuse un `speaker` égal au nom de la chaîne ou au titre de la vidéo.
- Le fichier de description liste les "voix citées" et ne mentionne plus la chaîne. `sources.md` (fichier privé)
  garde les liens minutés.
- **À faire après la v1 : repérer les extraits insérés dans la vidéo.** Beaucoup de vidéos intègrent des
  passages venus d'ailleurs (journal télévisé, interview, discours). Piste sans crédits : une détection locale
  des changements de voix (regroupement par empreinte vocale), qui marque dans la transcription compacte les
  paragraphes dits par une autre voix que la voix principale (`[autre voix]`). Claude sait alors où commence et
  finit un extrait, et le relecteur voit dans `plan.md` quelles citations restent sans voix identifiée.
  À évaluer pendant la campagne de tests.
