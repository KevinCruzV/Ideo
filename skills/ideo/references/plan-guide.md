# Guide d'écriture de plan.json

Lis ce guide une seule fois, en entier, avant d'écrire.

## 1. Le travail

D'après la transcription compacte d'une vidéo YouTube, tu écris `plan.json` : une vidéo verticale courte qui réexplique les idées principales (voix off, papier découpé). Chaque scène a un texte lu (`say`), un visuel (`type` + `props`) et des éléments qui apparaissent sur des mots du texte (`items`). Le code fait voix, minutage et rendu.

Langue : `"lang"` = la valeur de la ligne `Langue :`. TOUS les textes (`title`, `hook`, `question`, `say`, `props`) sont dans cette langue.

## 2. Choisir et construire

- Une seule partie dans `parts`, sauf si le contenu utile dépasse nettement 5 minutes de voix off (environ 750 mots de `say`) ou si l'utilisateur demande des parties : 8 au plus, chacune compréhensible seule.
- Durée : `Durée conseillée :` (en général 2 à 3 minutes) est un repère : plus court si l'histoire tient, plus long (300 s au plus) si elle en a besoin. Jamais haché : pour faire court, garde moins d'événements (les quatre ou cinq qui font l'histoire), ne les survole jamais tous. Durée estimée = mots de `hook`, `question` et des `say` / 3,0 (3,2 en anglais) + 0,5 s par scène + 3 s de fin + extraits audio. Entre 65 et 300 s (TikTok ne rémunère qu'au-delà d'une minute).
- Longueur, avant d'écrire : compte les idées nécessaires à la réponse de l'accroche (3 à 6 en général), 6 à 8 scènes chacune (d'où on part, ce qui se passe, ce que ça change), environ 25 s (4 idées, 100 s ; 6, 150 s). Au-delà de 180 s, retire l'idée la moins utile plutôt que de raccourcir chaque scène. Une idée qui ne tient pas en 3 scènes en prend une de plus.
- Une scène = une idée, 3 à 4 s (9 à 13 mots) : l'image change au moins 15 fois par minute. 80 scènes au plus.
- `"suspense": true` (à côté de `"type"`) sur une ou deux révélations fortes (chiffre qui choque, retournement) : la voix se tait 2 s avant. Jamais la première scène, jamais sur un sujet grave.

UNE histoire, pas des faits alignés :
- Scène 1 : le point de départ (date ou lieu ; sans chronologie, le problème concret que le spectateur reconnaît chez lui). Puis des actes dans l'ordre de la source, sans remonter le temps : un par chapitre utile de `Chapitres :`, sinon 2 à 4 (par époque, ou par thème, cas, organe, méthode).
- La scène qui ouvre un acte annonce son sujet, a le nom de l'acte dans `kicker` (avec une date : date dans `kicker`, nom dans le texte) et `"break": true` à côté de `"type"` (sauf la première scène) : vraie pause de voix, `kicker` en grand sur un carton plein écran la première seconde, donc court (« Acte 2 : le client »). Varie les transitions : question (« Et la Chine, alors ? »), conséquence (« Résultat : »), contraste (« Pendant ce temps, »).
- Chaque `say` dit son lien avec la scène d'avant (cause, conséquence, opposition, temps passé : "Résultat", "Mais dix ans plus tard", "C'est là que", "Face à ça", "Le problème"). Deux scènes qu'on peut échanger sans que ça se voie : il manque le lien.
- Date ou lieu dans la source : dans `kicker`, et l'année dans `say` si elle aide.
- Dernière scène : la réponse à l'accroche en une phrase claire, pas une ouverture vague.
- `title` : affiché en haut toute la vidéo, 40 caractères au plus (espaces compris).
- `src` de chaque scène : le `[mm:ss]` du paragraphe qui la justifie. Rien que la source : aucun fait, chiffre, nom ou date ajouté.
- Transcription automatique : un nom propre seulement si tu le reconnais avec certitude, bien orthographié, sinon le rôle ("le président de l'époque").
- Jamais de sponsor, promotion, appel à s'abonner ou vie de la chaîne : aucun minutage (`src`, citation, `sfx`) entre a et b d'une ligne `[passage sponsorisé a à b, ignoré]` ou `[passage probablement sponsorisé a à b, ignoré]`. Ne nomme jamais une marque ou un produit que la vidéo est payée pour promouvoir.
- Jamais le nom de la ligne `Chaîne :` ni de la personne qui anime la chaîne, nulle part (`title`, `hook`, `say`, `props`, citation) : si l'extrait le prononce, prends-en un autre. Le sujet et les mots de la ligne `Titre :` sont libres : tu peux les reprendre.

Récit d'histoire, de complot ou d'horreur seulement (jamais pour une explication de science, de santé, d'argent ou un guide pratique), ajoute :
- Ouverture par la fin, permise une fois : quand l'issue surprend (retournement, verdict, mort), les scènes 1 et 2 la donnent sans l'expliquer (« Le soir même, c'est sa rivale qui part en exil »), puis le premier acte remonte au début (« Pour comprendre, revenons 15 ans plus tôt ») et la suite reste dans l'ordre.
- Juste après l'ouverture, une scène peut promettre 2 ou 3 réponses précises tirées de la source, sans les donner (« une lettre jamais envoyée, et un témoin que personne n'a interrogé ») : chacune doit être donnée plus loin.
- Pose tôt le détail qui fera le dénouement (qui a aidé qui, un objet, une habitude), puis rappelle-le quand il sert : « Elle qui l'avait fait entrer au palais, c'est elle qui en sort. »
- Complot ou mystère (« qui a fait ça ? ») : raconte-le comme une enquête. Chaque piste a sa scène (« Premier suspect : le garde du corps »), ce qui l'accuse et ce qui la disculpe, puis un bilan des pistes écartées avant la dernière.
- Au moment clé, place le spectateur dans la scène : un détail concret du lieu ou de l'heure, puis « Mets-toi à sa place » ou « Imagine : tu es le guetteur ». Un compte à rebours tiré de la source tient bien (« Il lui reste 14 minutes »).
- Annonce une conséquence avant de la montrer (« Cette bagarre va lui coûter la vie »). En histoire ou en complot, une ironie sèche peut souligner un fait (« Et tout ça était parfaitement légal ») ; jamais en horreur ni sur des morts.
- Dernière phrase en deux moitiés qui s'opposent, pour qu'on la retienne : « Pour le tribunal, l'affaire est close. Pour les habitants, elle dure encore. »

## 3. L'accroche (`hook`)

- 6 à 10 mots, 60 caractères au plus (espaces compris), en général une question qui donne envie de connaître la réponse. Vraie, la vidéo y répond, aucun chiffre hors source. "Dis-moi pourquoi..." par défaut quand elle colle, sinon "Pourquoi... ?", "Tu sais ce qui se passe quand... ?", "Et si... ?", "Personne ne t'explique que...". En anglais : "Tell me why...?", "Why...?". Plusieurs parties : pas la même formule deux parties de suite. Exemples : "Pourquoi les avions ne volent pas en ligne droite ?", "Personne ne t'explique pourquoi la mer est salée." À éviter : chiffre inventé ("97 % des gens se trompent"), promesse vide sans sujet ("Le secret incroyable...").
- Histoire, fait divers, horreur ou biographie : pas de question, mais « Voici l'histoire de... » ou une phrase choc complète (« Il a fait croire à tout un pays qu'il était innocent »).
- Couverture : l'accroche est coupée au premier « , » ou « : » (avant : gros titre ; après : bande noire). Pour une histoire, le sujet avant la coupure (« L'histoire de Marvin Gaye, partie 1 : de l'église à Motown »). Dessin : photo de la première person-card avec photo, sinon son buste, sinon le premier picto non drapeau des 3 premières scènes, à choisir pour le sujet global (globe, pièces).

`question` (obligatoire) : question courte au spectateur en fin de partie, avant l'appel à s'abonner du code, sur le sujet et sur lui, pour qu'il réponde en commentaire. 60 caractères au plus, finit par « ? ». « Et toi, » sur ses habitudes (« Et toi, dans quelle position tu dors ? »), « Pour toi, » sur son avis (« Pour toi, quel pays aurait pu dominer à sa place ? »). Pas de question générale ("Ça t'a plu ?") ni de quiz dont la réponse est dans la vidéo.

## 4. Écrire pour la voix

`say` est lu par une voix de synthèse : écris comme on parle.
- 1 ou 2 phrases courtes, 9 à 13 mots, 20 au plus ; 15 mots au plus par phrase. Plus long : deux scènes qui se suivent, chacune son visuel.
- Nombres en chiffres, comme à l'écran ("en 2001", "3 000 personnes", "8 %", "1,3 milliard", "le 51e") : le code les fait dire en lettres. Seules les fractions s'écrivent en lettres ("un tiers", "la moitié").
- Dans `say` seulement : pas de parenthèses, pas d'unités abrégées ("nanomètres", pas "nm"), pas de symboles (%, €, &, /) ; sigles connus gardés ("OTAN", "BRICS", "ONU"). Les `props` peuvent en avoir.
- Phrases complètes, verbe précis : « ses empereurs protègent leur frontière nord des peuples des steppes », pas « préfèrent garder leur frontière nord ».
- Énumération lue : trois éléments au plus, les deux derniers reliés par « et » (« la variole, la rougeole et la grippe »).
- En français, tutoie le spectateur.
- `say` d'une `quote` : présente la citation sans la répéter (la vraie voix suit).
- Santé, argent, droit : garde les nuances ("souvent", "peut", "chez certains"), jamais un conseil comme une certitude ni une promesse de guérison, rien d'affirmé fort que la source ne justifie. Explique le mécanisme, laisse le spectateur choisir.
- Sujets graves (morts, attentat, guerre, maladie, fait divers, horreur, catastrophe) : ton sobre et grave du début à la fin, jamais joyeux, aucune formule légère, même après un moment positif. Pas de `counter` de victimes, pas de `mascot` en pose `content` ou `surprise`, pas de `sfx`. Prends `key-title`, `stamp` ou `timeline`.

### Écrire avec tes mots (anti-plagiat)

- Mêmes chiffres, dates, noms et faits que la source ; autres mots, autre construction : « En moyenne, on change de position entre 10 et 40 fois par nuit » devient « Chaque nuit, ton corps bouge 10 à 40 fois sans que tu le saches ».
- Pas phrase par phrase : regroupe deux idées, coupe les détails, change l'ordre quand le sens le permet.
- `check` refuse 10 mots de suite identiques à la source dans `say`, `hook` ou `question`, et une partie dont plus de 20 % du texte reprend des suites de 5 mots de la source. Une liste de lieux, un nom propre long ou une date passent si le reste de la phrase est à toi.
- Seule la citation (`quote`, `props.text`) reprend la source mot pour mot.

### Écrire sans tics d'IA (filtre anti-slop)

Dans `hook`, `say` et les textes à l'écran :
- Aucun tiret long (cadratin ou demi-cadratin), double trait (`--`) ou trait d'union isolé entre deux espaces : point, virgule ou deux-points. Les mots composés gardent leur trait d'union (« États-Unis »).
- Pas de mots creux (« révolutionnaire », « incroyable », « fascinant », « véritable », « crucial », « essentiel », « au cœur de », « un monde où », « une nouvelle ère », « changer la donne ») : dis le fait précis.
- Pas d'annonce (« Plongeons », « Voyons ensemble », « Dans cette vidéo », « Tu vas voir que ») ni de fausse confidence (« Honnêtement », « Soyons clairs », « Spoiler », « Le truc, c'est que »).
- « Ce n'est pas X, c'est Y » ou « Non seulement X, mais aussi Y » : une fois par vidéo au plus.
- Pas trois phrases de trois mots de suite (une phrase courte pour appuyer, oui).
- Pas de liste forcée à trois : autant d'éléments que la source. Une reprise du même début de phrase sur des scènes qui se suivent (« Elle qui l'a repéré. Elle qui l'a fait nommer. ») : une fois par vidéo au plus, sur des faits de la source.
- « Spoiler » reste interdit, mais dans un récit d'histoire, de complot ou d'horreur, annoncer une conséquence précise avant de la montrer est permis (section 2).
- Pas de conclusion vague (« L'avenir nous le dira », « Une chose est sûre », « À méditer ») : finis sur la réponse concrète.
- Pas de majuscules pour crier dans `say`, pas de guillemets pour souligner.
- Un sujet qui agit : « les chercheurs ont mesuré », pas « il a été montré ».

## 5. Les 17 types de scène

Recopie exactement les noms de props et de `el`. * = obligatoire ; omets une prop facultative si la source ne donne rien, n'invente pas. `counter.to`, `counter.from` et `shape-diagram.values` : nombres sans guillemets. Textes à l'écran : chiffres permis, plafond espaces compris entre crochets ([28 caractères] = 28 au plus). Dans `el`, N devient un numéro : `chips.0`, jamais `chips.N`.

| type | quand l'utiliser | props | `el` possibles |
|---|---|---|---|
| `key-title` | la phrase-clé d'une idée | `text`* [90 caractères] ; `accent` [40 caractères] : mot(s) recopié(s) de `text`, sur la bande de couleur ; `kicker`, `picto` | `text`, `accent` |
| `person-card` | qui a dit ou fait quoi, en personnage de papier | `name`* [48 caractères] ; `role` [100 caractères] ; `picto` (drapeau de son pays) ; apparence `gender`, `age`, `job`, `hair`, `hair_color`, `facial`, `hat`, `glasses`, `outfit`, `skin` ; `photo` ; `kicker` | `avatar`, `name`, `role` |
| `fact-chips` | 2 à 6 faits courts qui s'ajoutent | `chips`* : textes (6 max) [28 caractères chacun] ; `kicker`, `picto` | `chips.0` à `chips.5` |
| `stack-list` | étapes ou raisons qui s'accumulent | `items`* : textes (5 max) [60 caractères chacun] ; `kicker`, `picto` | `items.0` à `items.4` |
| `counter` | un nombre qui monte | `to`* : nombre d'arrivée ; `from` : départ (0 par défaut), visible dès la première image ; `label` [60 caractères] : ce qu'on compte ; `unit` [4 caractères] ("%", "x", "km") ; `kicker`, `picto` | `to` (lance le compte : un des premiers mots du `say`), `label` |
| `timeline` | une chronologie | `marks`* : `{at, label}` (5 max, `at` obligatoire) [`at` 12 caractères, `label` 48 caractères] ; `start`, `end` [30 caractères] ; `kicker`, `picto` | `marks.0` à `marks.4` |
| `icon-grid` | des catégories, une famille | `cells`* : `{shape, label}` (9 max, `label` obligatoire) [`label` 16 caractères], `shape` = `circle`, `square`, `triangle`, `diamond`, `arrow` ou `strip`, ou un `picto` à sa place ; `kicker` | `cells.0` à `cells.8` |
| `stamp` | conclusion forte, idée reçue démentie | `text`* [48 caractères] (en majuscules) ; `kicker`, `picto` | `text` |
| `quote` | une phrase exacte de la source, avec sa vraie voix | `text`* [200 caractères], `speaker` [32 caractères] (section 7) ; `kicker`, `picto` | `text`, `speaker` |
| `object-state` | un objet qui change d'état | `object`* = `screen`, `board` (texte dedans), `phone` (une bulle SMS par état), `jar` (se remplit), `door` (s'ouvre), `scale` (penche), `battery` (se charge), `gauge` (aiguille), `lights` (feu rouge, jaune, bleu) ou `plant` (pousse) ; `states`* : textes (6 max) [36 caractères chacun], le premier visible dès le début, chaque suivant le remplace sur son mot ; `kicker` | `states.1` à `states.5` |
| `shape-diagram` | comparer des tailles ou des quantités | `values`* : nombres (8 max), chaque forme à la taille de sa valeur ; `shape` = `circle`, `square`, `triangle` ou `bar` (barres, valeur et `unit` au-dessus) ; `labels` [14 caractères chacun], autant que `values` ; `unit` [8 caractères] ("Md$", "%", "km"), toujours donnée si la valeur en a une ; `kicker` | `values.0` à `values.7`, `labels.0` à `labels.7` |
| `mascot` | le personnage Ideo qui réagit | `bubble`* [80 caractères] ; `pose` = `question` (défaut : question naïve du spectateur), `surprise` (fait contre l'intuition), `montre` (désigne la suite) ou `content` (leçon à retenir) ; `kicker` | `bubble` |
| `versus` | deux camps, options ou époques face à face | `left`*, `right`* [24 caractères chacun] ; `left_picto`, `right_picto` ; `kicker` | `left`, `right` |
| `map` | où ça se passe : pays, région, route | `focus`* = `world`, `europe`, `africa`, `asia`, `north-america`, `south-america`, `middle-east`, `oceania` ou `arctic` ; `places`* : `{code, label}` (6 max), `code` = code pays à deux lettres, `label` [24 caractères] ; `route` : 2 à 6 codes reliés dans l'ordre ; `kicker` | `places.0` à `places.5`, `route` |
| `body` | le corps : posture, geste, organe | `pose`* = `standing`, `sitting`, `walking`, `running`, `lying-back`, `lying-starfish`, `lying-side-left`, `lying-side-right`, `lying-fetal` ou `lying-stomach` ; `setting` = `none`, `bed`, `chair`, `desk` ou `outdoor` ; `marks` : `{part, label}` (4 max), `part` = `head`, `brain`, `neck`, `throat`, `shoulders`, `chest`, `heart`, `lungs`, `stomach`, `back`, `spine`, `hips`, `arms`, `hands`, `knees`, `legs` ou `feet`, `label` [28 caractères] ; `tone` = `good` (bleu), `bad` (rouge) ou `neutral` ; `kicker` | `marks.0` à `marks.3` |
| `artwork` | œuvre d'art citée (tableau, dessin, sculpture) ou logo d'une marque citée | `title`* [48 caractères] : titre ou marque ; `artist` [40 caractères] (vide pour un logo) ; `kicker` | `title`, `artist` |
| `image` | une vraie photo en grand : lieu, objet, animal, machine, événement | `query`* : la recherche en anglais lancée avec `ideo image`, recopiée exactement ; `caption` [40 caractères] : légende courte ; `kicker` | `caption` |

- `kicker` [28 caractères], tous types : étiquette visible dès la première image : date, lieu ou nom de l'acte ("1991", "Irak, 2003", "Acte 2 : les BRICS").
- `picto` (`key-title`, `fact-chips`, `stack-list`, `counter`, `timeline`, `stamp`, `quote`, cellules d'`icon-grid`) : dessin visible dès la première image, qui montre la chose dont parle la scène, pas un symbole vague. Aucun ne convient : pas de `picto` approximatif, note le manque dans `"wishes"` (premier niveau, à côté de `"parts"`, 0 à 5 textes [40 caractères], par exemple `"wishes": ["carte du monde"]`).
- `kicker` et `picto` ne sont pas des `el` : jamais dans `items`.

`person-card` : apparence d'après ce qui rend la personne reconnaissable, seulement ce dont tu es sûr, mais jamais aucune prop. Deux personnes différentes n'ont jamais la même apparence.
- `gender` : `woman`, `man` ; `age` : `child`, `adult`, `old` ; `job` (tenue et couvre-chef) : `police`, `firefighter`, `doctor`, `judge`, `soldier`, `worker`, `journalist`, `lawyer`
- `hair` : `none`, `short`, `side`, `long`, `curly`, `wild`, `bun`, `crown-bald` ; `hair_color` : `black`, `brown`, `blond`, `red`, `grey`, `white`
- `facial` : `none`, `moustache`, `beard`, `goatee`, `sideburns` ; `glasses` : `true` ou `false`
- `hat` : `none`, `cap`, `kepi`, `bicorne`, `crown`, `helmet`, `top-hat`, `beret`, `turban`, `laurel`, `wig`
- `outfit` : `suit`, `uniform`, `robe`, `lab-coat`, `casual`, `toga`, `armor`, `dress` ; `skin` : `light`, `tan`, `brown`, `dark`
Exemple, un savant aux cheveux blancs en bataille : `"hair": "wild", "hair_color": "white", "facial": "moustache", "outfit": "lab-coat"`. Biographie ou histoire : la personne principale a une seule `person-card` (pas une par acte) ; ne répète ni son nom ni sa photo, garde la même apparence si une autre carte la montre.

Collages : personne historique connue (savant, chef d'État, artiste), jamais dans un fait divers ni pour une personne privée : `ideo photo JOB "<nom>"` une fois par personne avant d'écrire. Si la réponse n'est pas « aucune photo libre », `"photo": true` sur ses cartes (`name` = son nom), sinon portrait en papier. Œuvre citée : `ideo photo JOB "<titre>"`, scène `artwork` seulement si l'image est trouvée, ce titre dans `title`. Marque citée : `ideo photo JOB "<marque>"`, scène `artwork` avec son nom dans `title`, sans `artist`.

Photos : un lieu, un objet, un animal, une machine ou un événement que le spectateur gagne à voir en vrai, ou une chose qu'aucun `picto` ne montre (au lieu de `"wishes"`). Avant d'écrire, une seule commande pour toutes les recherches : `ideo image JOB "eiffel tower" "oil rig"` (2 à 4 mots anglais concrets par recherche). Chaque ligne `OK image : « <recherche> » : aucune image` : pas de scène `image` pour elle. Sinon, scène `image` avec cette recherche dans `query`. Au plus 1 scène sur 4, jamais deux de suite, jamais pour montrer une personne (c'est `person-card`).

Drapeaux : partout où `picto` est accepté, `flag:` + code pays à deux lettres en minuscules, pour tous les pays (`flag:fr`, `flag:us`, `flag:iq`). Aussi `flag:eu` (Union européenne), `flag:un` (ONU), `flag:su` (Union soviétique), et pour une région `flag:gb-sct` (Écosse), `flag:gb-eng` (Angleterre), `flag:gb-wls` (pays de Galles), `flag:gb-nir` (Irlande du Nord), `flag:es-ct` (Catalogne), jamais le drapeau du voisin. Jamais de drapeau dans `wishes`. Pays nommé à l'écran : son drapeau. `say` qui cite trois pays ou plus : `icon-grid`, un drapeau et un nom par cellule. `versus` entre deux pays : un drapeau de chaque côté.

Premier niveau du plan, à côté de `"parts"`, seulement si ça s'applique :
- `"mood": "dark"` (fait divers, crime, horreur, catastrophe) : fonds et papiers sombres.
- `"paper"` : `"kraft"` (argent, économie), `"journal"` (histoire, politique, fait divers, horreur), `"millimetre"` (science, santé), `"album"` (biographie). Les supports (ticket, coupure, post-it) sont choisis par le code.
- `"ton": "pose"` (biographie, histoire, fait divers, sujet grave) : voix posée en version finale. Sinon, voix dynamique.

Jeu de la voix finale (balise ElevenLabs v3, en anglais) : `"jeu"` sur une scène, `"jeu_hook"` et `"jeu_question"` sur la partie, une seule balise parmi `curious`, `excited`, `whispers`, `sighs`, `laughs`, `sarcastic`, `surprised`, `serious`, `mischievously`, `sad`. Elle joue tout le `say`. Mets `jeu_hook` (souvent `curious`) et `jeu_question` (souvent `curious` ou `excited`), puis 2 à 4 scènes au plus, là où l'émotion change vraiment : `whispers` avant un secret, `surprised` sur un chiffre qui choque, `sighs` sur un constat triste, `laughs` sur une absurdité. Sujet grave : `serious` ou `sad`, jamais `laughs`. Pas de balise dans le texte lui-même.

Valeurs de `picto` (recopie le nom exact) : `globe`, `flag`, `pin`, `city`, `house`, `factory`, `bank`, `coin`, `chart-up`, `chart-down`, `ship`, `plane`, `train`, `rocket`, `satellite`, `tank`, `shield`, `sword`, `bomb`, `dove`, `handshake`, `justice`, `wall`, `chain`, `lock`, `key`, `crown`, `ballot`, `megaphone`, `newspaper`, `tv`, `phone`, `computer`, `chip`, `book`, `brain`, `heart`, `eye`, `clock`, `calendar`, `lightbulb`, `atom`, `flask`, `leaf`, `sun`, `drop`, `fire`, `lightning`, `mountain`, `barrel`, `gear`, `people`, `lungs`, `stomach`, `spine`, `bone`, `muscle`, `tooth`, `blood`, `pill`, `syringe`, `virus`, `bed`, `pillow`, `moon`, `thermometer`, `scale-weight`, `apple`, `dumbbell`, `running-shoe`, `stethoscope`, `hospital`, `raised-bed`, `stomach-sleeper`, `knee-pillow`, `snore`, `pelvis-tilt`, `numb-arm`, `blood-stain`, `chalk-outline`, `crime-tape`, `handcuffs`, `knife`, `coffin`, `tombstone`, `mirror`, `mars`, `music-note`, `vinyl`, `microphone`, `ankle-monitor`, `hemicycle`, `credit-rating`, `constitution`, `broken-car`, `hourglass`, `ghost`, `camper-van`, `envelope`, `video-phone`. Un même picto revient au plus 2 fois par vidéo. La ligne `OK prepare` liste les dessins déjà utilisés dans les 3 dernières vidéos (un `object` d'`object-state` s'écrit `object:scale`) : évite-les, et `check` te signale ceux qui reviennent.

Un écran apprend quelque chose seul, sans le son : chaque texte d'une liste (`chips`, `items`, `label` de cellule) dit un fait complet avec un chiffre ou un verbe ("8 % dorment sur le dos", pas "Sur le dos" ; "BRICS, créés en 2011" avec un `picto`, pas "Russie", "Inde", "Chine").

Ces exemples viennent d'une autre vidéo : n'en recopie ni les textes ni les minutages.

Un exemple par type :

```json
{"type": "key-title", "say": "Ce que tu oublies le plus vite, c'est ce que tu n'as jamais révisé.", "props": {"kicker": "Allemagne, 1885", "picto": "brain", "text": "La courbe de l'oubli", "accent": "l'oubli"}, "items": [{"el": "text", "on": "oublies"}, {"el": "accent", "on": "révisé"}], "src": "0:12"}
{"type": "person-card", "say": "Le psychologue allemand Hermann Ebbinghaus a testé sa propre mémoire pendant des mois.", "props": {"name": "Hermann Ebbinghaus", "role": "Psychologue allemand, 1885"}, "items": [{"el": "avatar", "on": "psychologue"}, {"el": "name", "on": "Ebbinghaus"}, {"el": "role", "on": "mémoire"}], "src": "1:05"}
{"type": "fact-chips", "say": "Il apprenait des syllabes sans aucun sens, par listes de treize, jusqu'à les réciter sans erreur.", "props": {"chips": ["Syllabes sans sens", "Listes de 13", "Zéro erreur"]}, "items": [{"el": "chips.0", "on": "syllabes"}, {"el": "chips.1", "on": "listes"}, {"el": "chips.2", "on": "erreur"}], "src": "1:40"}
{"type": "stack-list", "say": "Révise juste avant d'oublier. Espace tes révisions. Et teste-toi au lieu de relire.", "props": {"items": ["Réviser avant d'oublier", "Espacer", "Se tester"]}, "items": [{"el": "items.0", "on": "Révise"}, {"el": "items.1", "on": "Espace"}, {"el": "items.2", "on": "teste-toi"}], "src": "6:10"}
{"type": "counter", "say": "Au total, il a appris plus de 2 000 syllabes inventées.", "props": {"picto": "book", "label": "syllabes apprises", "from": 0, "to": 2300}, "items": [{"el": "to", "on": "appris"}, {"el": "label", "on": "syllabes"}], "src": "2:02"}
{"type": "timeline", "say": "Son expérience date du dix-neuvième siècle, et des chercheurs l'ont refaite récemment avec le même résultat.", "props": {"start": "1880", "end": "2020", "marks": [{"at": "1885", "label": "Ebbinghaus publie"}, {"at": "2015", "label": "Expérience refaite"}]}, "items": [{"el": "marks.0", "on": "siècle"}, {"el": "marks.1", "on": "récemment"}], "src": "4:30"}
{"type": "icon-grid", "say": "Quatre choses aident la mémoire : le sommeil, la répétition, l'émotion et le sens.", "props": {"cells": [{"shape": "circle", "label": "Sommeil"}, {"shape": "square", "label": "Répétition"}, {"shape": "triangle", "label": "Émotion"}, {"shape": "diamond", "label": "Sens"}]}, "items": [{"el": "cells.0", "on": "sommeil"}, {"el": "cells.1", "on": "répétition"}, {"el": "cells.2", "on": "émotion"}, {"el": "cells.3", "on": "sens"}], "src": "5:15"}
{"type": "stamp", "say": "Relire ses notes la veille ne suffit pas. C'est même la méthode la moins efficace.", "props": {"text": "Relire ne suffit pas"}, "items": [{"el": "text", "on": "suffit"}], "src": "5:50"}
{"type": "quote", "say": "Une chercheuse interrogée sur France Culture le dit simplement.", "props": {"text": "on n'oublie pas par paresse, le cerveau fait du tri", "speaker": "France Culture"}, "items": [{"el": "text", "on": "dit"}, {"el": "speaker", "on": "simplement"}], "src": "3:12"}
{"type": "object-state", "say": "À chaque révision, le souvenir tient plus longtemps, et le bocal se remplit.", "props": {"object": "jar", "states": ["1re révision", "2e révision", "3e révision"]}, "items": [{"el": "states.1", "on": "souvenir"}, {"el": "states.2", "on": "remplit"}], "src": "6:40"}
{"type": "shape-diagram", "say": "Juste après la leçon, tu retiens tout. Un jour plus tard, il reste à peine un tiers.", "props": {"shape": "circle", "values": [1, 0.34], "labels": ["Juste après", "Le lendemain"]}, "items": [{"el": "values.0", "on": "leçon"}, {"el": "labels.0", "on": "retiens"}, {"el": "values.1", "on": "jour"}, {"el": "labels.1", "on": "tiers"}], "src": "2:30"}
{"type": "mascot", "say": "Alors, réviser la veille de l'examen, ça ne sert à rien ?", "props": {"bubble": "Et réviser la veille ?", "pose": "question"}, "items": [{"el": "bubble", "on": "réviser"}], "src": "5:40"}
{"type": "map", "say": "Ebbinghaus travaille à Berlin, en Allemagne, et ses résultats traversent vite l'Atlantique jusqu'aux États-Unis.", "props": {"kicker": "1885", "focus": "world", "places": [{"code": "de", "label": "Berlin"}, {"code": "us", "label": "États-Unis"}], "route": ["de", "us"]}, "items": [{"el": "places.0", "on": "Berlin"}, {"el": "route", "on": "traversent"}, {"el": "places.1", "on": "États-Unis"}], "src": "1:20"}
{"type": "body", "say": "Quand tu dors, ton cerveau trie ce que tu as appris. Allongé sur le dos, ta respiration ralentit et ton cœur aussi.", "props": {"kicker": "Pendant la nuit", "pose": "lying-back", "setting": "bed", "tone": "good", "marks": [{"part": "brain", "label": "Il trie les souvenirs"}, {"part": "heart", "label": "Il ralentit"}]}, "items": [{"el": "marks.0", "on": "cerveau"}, {"el": "marks.1", "on": "cœur"}], "src": "5:20"}
{"type": "versus", "say": "D'un côté, relire dix fois la même page. De l'autre, fermer le livre et se poser des questions.", "props": {"kicker": "Deux méthodes", "left": "Relire", "left_picto": "book", "right": "Se tester", "right_picto": "brain"}, "items": [{"el": "left", "on": "relire"}, {"el": "right", "on": "questions"}], "src": "5:58"}
{"type": "artwork", "say": "En 1889, il peint La nuit étoilée depuis la fenêtre de l'asile où il vit.", "props": {"kicker": "1889", "title": "La nuit étoilée", "artist": "Vincent van Gogh"}, "items": [{"el": "title", "on": "peint"}, {"el": "artist", "on": "fenêtre"}], "src": "4:20"}
{"type": "image", "say": "La plateforme pompe le pétrole à trois cents mètres sous la mer du Nord.", "props": {"kicker": "Mer du Nord", "query": "oil rig", "caption": "Une plateforme pétrolière"}, "items": [{"el": "caption", "on": "pompe"}], "src": "4:40"}
```

## 6. `items[].on` : quand un élément apparaît

- Chaque élément apparaît sur le mot de `on` : un mot ou une courte suite de mots recopiés exactement du `say` de la scène. Un élément absent de `items` est visible dès la première image. Liste tous les éléments sauf `states.0` (visible dès le début) et `speaker` vide.
- `items` dans l'ordre où leurs mots sont dits ; deux éléments peuvent partager un mot.
- Premier élément sur un des premiers mots du `say` (le code le montre de toute façon au début), dernier sur un mot de la dernière phrase, sinon l'écran reste figé pendant que la voix continue.

## 7. Citations et sons

- `quote` joue la vraie voix de la source. `props.text` = des mots recopiés exactement, dans l'ordre, d'un seul paragraphe, jamais traduits. Seule correction : recoller apostrophes et traits d'union ("c 'est" donne "c'est", "est -il" donne "est-il"). 8 secondes au plus, environ 20 mots. `src` = le `[mm:ss]` de ce paragraphe.
- `speaker` = qui on entend, comme la transcription le dit : "Prénom Nom", "Prénom Nom, média" ou le média seul. L'indice est dans le texte autour d'un extrait inséré (journal télé, interview, discours) : "comme l'expliquait Hubert Reeves sur France Inter" donne `"speaker": "Hubert Reeves, France Inter"`.
- Personne nommée, ou seulement "un journal", "un reportage" : `"speaker": ""`. Pas de crédit vaut mieux qu'un faux. Jamais le nom de la chaîne YouTube, le titre de la vidéo, le présentateur ("je suis Léa") ni un nom inventé.
- Une `quote` n'est jamais le présentateur qui lit un texte (lettre, article) : il faut un extrait où la source passe la voix à quelqu'un d'autre, sinon le texte va dans un `stamp` ou dans le `say`.
- Une ligne `[son 2:43 2.5s]` est un son sans parole. Pour le jouer après le `say` d'une scène : `"sfx": "2:43"` (le minutage après `son`). Zéro à deux par vidéo (trois au plus pour la biographie d'un artiste musical), 10 secondes au plus, seulement si le `say` parle de ce moment, jamais sur un sujet grave ni sur une `quote`. La section 9 montre une `quote` (`src` 1:55, `speaker` vide) et un `sfx`.

## 8. Variété

- Jamais deux fois de suite le même type.
- `key-title` : 1 par acte au plus. `mascot` : 4 par vidéo au plus, jamais deux de suite. `versus` : 2 par vidéo au plus.
- Au moins une scène sur deux montre un dessin : `picto`, `object-state`, `versus`, `shape-diagram`, `timeline`, `map`, `body` ou `mascot`.
- Corps (santé, sommeil, sport, posture, organe) : des `body` avec la posture et les zones en `marks`. Lieu qui compte (pays, trajet, frontière) : une `map`. Deux camps, deux époques, avant et après : `versus` ou `object-state`. Trois dates ou plus : `timeline`. Deux nombres à comparer : `shape-diagram` avec `unit`.
- Une `quote` toutes les 8 à 10 scènes si la source a des extraits nets (journal, discours, interview) ; un seul extrait, une seule ; aucun, aucune.
- Pas trois `say` de suite qui commencent par le même mot.

## 9. Exemple complet

Source : une vidéo française de 3 min 49 sur la couleur du ciel. Une vidéo de 13 scènes, environ 100 s. Regarde comment chaque `say` s'accroche au précédent et comment la dernière scène répond à l'accroche.

```json
{
  "version": 1,
  "lang": "fr",
  "series_title": "Pourquoi le ciel est bleu",
  "parts": [
    {
      "n": 1,
      "title": "Pourquoi le ciel est bleu",
      "hook": "Dis-moi pourquoi le ciel est bleu et pas violet ?",
      "question": "Et toi, tu regardes souvent le ciel au coucher du soleil ?",
      "scenes": [
        {
          "type": "key-title",
          "say": "La lumière du soleil est blanche. Pourtant, au-dessus de ta tête, le ciel est bleu.",
          "props": {"picto": "sun", "text": "Une lumière blanche, un ciel bleu", "accent": "bleu"},
          "items": [{"el": "text", "on": "blanche"}, {"el": "accent", "on": "bleu"}],
          "src": "0:02"
        },
        {
          "type": "shape-diagram",
          "say": "En réalité, cette lumière mélange toutes les couleurs, et chacune est une onde : longue pour le rouge, courte pour le violet.",
          "props": {"kicker": "Longueur d'onde", "shape": "bar", "values": [700, 400], "labels": ["rouge", "violet"], "unit": "nm"},
          "items": [
            {"el": "values.0", "on": "longue"},
            {"el": "labels.0", "on": "rouge"},
            {"el": "values.1", "on": "courte"},
            {"el": "labels.1", "on": "violet"}
          ],
          "src": "0:25"
        },
        {
          "type": "fact-chips",
          "say": "En entrant dans l'air, elle croise des milliards de molécules d'azote et d'oxygène, bien plus petites que ces ondes.",
          "props": {"picto": "atom", "chips": ["Des milliards de molécules", "Azote et oxygène", "Plus petites que l'onde"]},
          "items": [
            {"el": "chips.0", "on": "milliards"},
            {"el": "chips.1", "on": "azote"},
            {"el": "chips.2", "on": "petites"}
          ],
          "src": "0:49"
        },
        {
          "type": "counter",
          "say": "Résultat : plus l'onde est courte, plus elle rebondit, et le bleu rebondit plus de 5 fois plus que le rouge.",
          "props": {"label": "fois plus de bleu renvoyé", "from": 1, "to": 5},
          "items": [{"el": "to", "on": "bleu"}, {"el": "label", "on": "rouge"}],
          "src": "1:11"
        },
        {
          "type": "person-card",
          "say": "Ce phénomène porte le nom du physicien anglais Lord Rayleigh, qui l'a mis en équation au dix-neuvième siècle.",
          "props": {"kicker": "1871", "name": "Lord Rayleigh", "role": "Physicien anglais", "picto": "flag:gb", "facial": "beard", "hair": "crown-bald", "outfit": "suit"},
          "items": [
            {"el": "avatar", "on": "physicien"},
            {"el": "name", "on": "Lord Rayleigh"},
            {"el": "role", "on": "équation"}
          ],
          "src": "1:32"
        },
        {
          "type": "quote",
          "say": "Une physicienne de l'atmosphère le résume en une phrase.",
          "props": {"text": "Le ciel n'est pas peint en bleu, c'est de la lumière du soleil renvoyée vers nous", "speaker": ""},
          "items": [{"el": "text", "on": "résume"}],
          "src": "1:55"
        },
        {
          "type": "mascot",
          "say": "Mais alors, si le violet rebondit encore plus, pourquoi le ciel n'est pas violet ?",
          "props": {"bubble": "Et pourquoi pas violet ?"},
          "items": [{"el": "bubble", "on": "pourquoi"}],
          "src": "2:11"
        },
        {
          "type": "stack-list",
          "say": "Le soleil envoie moins de violet. Le haut de l'atmosphère en absorbe une partie. Et tes yeux voient mieux le bleu.",
          "props": {"kicker": "Trois raisons", "items": ["Le soleil envoie moins de violet", "L'atmosphère en absorbe", "Nos yeux préfèrent le bleu"]},
          "items": [
            {"el": "items.0", "on": "soleil"},
            {"el": "items.1", "on": "absorbe"},
            {"el": "items.2", "on": "yeux"}
          ],
          "src": "2:11"
        },
        {
          "type": "object-state",
          "say": "Chez toi, éclaire un verre d'eau avec quelques gouttes de lait : vu de côté, il devient bleuté.",
          "props": {"object": "jar", "states": ["Eau et lait", "Vu de côté : bleuté"]},
          "items": [{"el": "states.1", "on": "bleuté"}],
          "sfx": "2:43",
          "src": "2:33"
        },
        {
          "type": "shape-diagram",
          "say": "Et le soir, alors ? La lumière traverse jusqu'à 40 fois plus d'air qu'à midi. Le bleu se perd en route, il reste le rouge.",
          "props": {"kicker": "Coucher de soleil", "shape": "square", "values": [1, 40], "labels": ["midi", "soir"]},
          "items": [
            {"el": "values.1", "on": "soir"},
            {"el": "labels.1", "on": "soir"},
            {"el": "values.0", "on": "midi"},
            {"el": "labels.0", "on": "midi"}
          ],
          "src": "3:00"
        },
        {
          "type": "stamp",
          "say": "Et non, le ciel ne reflète pas la mer. Il est aussi bleu au-dessus du désert.",
          "props": {"text": "Reflet de la mer : faux"},
          "items": [{"el": "text", "on": "mer"}],
          "src": "3:20"
        },
        {
          "type": "icon-grid",
          "say": "Sur Mars, la poussière inverse tout : le ciel est couleur caramel le jour, et bleu au coucher du soleil.",
          "props": {"kicker": "Sur Mars", "cells": [{"picto": "globe", "label": "Mars"}, {"picto": "sun", "label": "Jour : caramel"}, {"shape": "diamond", "label": "Soir : bleu"}]},
          "items": [
            {"el": "cells.0", "on": "Mars"},
            {"el": "cells.1", "on": "caramel"},
            {"el": "cells.2", "on": "coucher"}
          ],
          "src": "3:33"
        },
        {
          "type": "mascot",
          "say": "Donc le ciel est bleu parce que l'air renvoie surtout le bleu, et que tes yeux le voient mieux que le violet.",
          "props": {"bubble": "L'air renvoie surtout le bleu", "pose": "content"},
          "items": [{"el": "bubble", "on": "renvoie"}],
          "src": "2:11"
        }
      ]
    }
  ]
}
```

Avec plusieurs parties : ajoute des objets dans `parts` avec `"n": 2`, `"n": 3`, chacun avec son `title`, son `hook` et ses `scenes`. Quand une vidéo réunit plusieurs sujets différents mais liés, la scène 1 annonce le fil conducteur et chaque début de partie dit en une phrase le lien avec la précédente.

## 10. Erreurs de `check`

Chaque ligne de `check` commence par l'endroit ("Plan", "Partie 1", "Partie 1, scène 4") et dit quoi corriger : corrige seulement ce qu'elle nomme. `n'a pas de voix de synthèse` : ne corrige rien, montre l'erreur à l'utilisateur et arrête-toi.
