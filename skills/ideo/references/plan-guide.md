# Guide d'écriture de plan.json

Lis ce guide une seule fois, en entier, avant d'écrire.

## 1. Le travail

Tu lis la transcription compacte d'une vidéo YouTube et tu écris `plan.json` : une vidéo verticale courte qui réexplique les idées principales, avec une voix off et des formes en papier découpé. Chaque scène a un texte dit à voix haute (`say`), un visuel (`type` + `props`) et des éléments qui apparaissent sur des mots du texte (`items`). Tout le reste (voix, minutage, rendu) est fait par le code.

Langue : mets dans `"lang"` la valeur de la ligne `Langue :` de la transcription, et écris TOUS les textes (`title`, `hook`, `question`, `say`, textes des `props`) dans cette langue.

## 2. Choisir et construire

- Une seule vidéo (une seule partie dans `parts`). Plusieurs parties seulement si le contenu utile dépasse nettement 5 minutes de voix off (environ 750 mots de `say`), ou si l'utilisateur demande des parties : 8 parties au maximum, chacune compréhensible seule.
- Durée : la ligne `Durée conseillée :` en tête de la transcription donne un repère, en secondes et en mots de `say` (en général 2 à 3 minutes). Ce n'est pas une obligation : plus court est très bien si l'histoire tient, plus long (jusqu'à 300 s) si elle en a besoin. La seule règle : la vidéo ne doit jamais paraître hachée. Une vidéo courte se fait en gardant moins d'événements, jamais en les survolant tous. Durée estimée = mots de `hook`, de `question` et de tous les `say` divisés par 3,0 (3,2 en anglais), plus 0,5 s par scène, plus 3 s de fin, plus la durée des extraits audio. Entre 65 et 300 s : TikTok ne rémunère que les vidéos de plus d'une minute.
- Juge toi-même la longueur, avant d'écrire, en comptant les idées :
  1. Liste dans ta tête les idées sans lesquelles on ne comprend pas la réponse à l'accroche. En général 3 à 6.
  2. Chaque idée demande 6 à 8 scènes courtes : d'où on part, ce qui se passe, ce que ça change. Soit 20 à 30 s par idée.
  3. Longueur = nombre d'idées x 25 s environ. 4 idées font une vidéo d'environ 100 s, 6 idées environ 150 s.
  4. Si le total dépasse 180 s, retire l'idée la moins utile plutôt que de raccourcir chaque scène. Si une idée ne tient pas en 3 scènes, donne-lui-en une de plus.
- Repère : une scène dure 3 à 4 s (9 à 13 mots) : l'image change au moins 15 fois par minute, comme les vidéos courtes qui retiennent. 80 scènes au plus.
- Une idée par scène. Ne survole jamais dix événements : choisis les quatre ou cinq qui font l'histoire.
- Suspense : sur une ou deux révélations fortes (le chiffre qui choque, le retournement), ajoute `"suspense": true` à la scène qui révèle, à côté de `"type"` : la voix se tait 2 s juste avant. Deux scènes au plus par vidéo, jamais la première, jamais sur un sujet grave (section 4).

La vidéo raconte UNE histoire, elle n'aligne pas des faits :
- Scène 1 : le point de départ. Pour une histoire, sa date ou son lieu. Pour un sujet sans chronologie (science, santé, méthode), le problème concret que le spectateur reconnaît chez lui.
- Ensuite, des actes, toujours dans l'ordre de la source : ne remonte jamais dans le temps de la vidéo. Si la transcription a une liste `Chapitres :`, fais un acte par chapitre utile, dans leur ordre. Sinon, découpe toi-même en 2 à 4 actes : par époque pour une histoire, par thème ou par cas pour un sujet sans chronologie (un acte par position, par organe, par méthode). Ouvre chaque acte par une scène qui annonce de quoi il parle, et mets le nom de l'acte dans son `kicker`. Si cette scène a aussi une date, la date va dans le `kicker` et le nom de l'acte dans le texte de la scène. Ajoute `"break": true` à cette scène, à côté de `"type"` (sauf pour la toute première scène) : la voix marque alors une vraie pause avant de changer de sujet. Son `kicker` s'affiche alors en grand, sur un carton plein écran, pendant la première seconde de la scène : garde-le court (« Acte 2 : le client »). Entre deux sujets, varie la transition à chaque fois : une question (« Et la Chine, alors ? »), une conséquence (« Résultat : ») ou un contraste (« Pendant ce temps, »).
- Chaque `say` part de la scène d'avant : dis ce qui relie les deux (la cause, la conséquence, l'opposition, le temps passé). Exemples de liens : "Résultat", "Mais dix ans plus tard", "C'est là que", "Face à ça", "Le problème". Si on peut mélanger deux scènes sans que ça se voie, il manque le lien.
- Quand un événement a une date ou un lieu dans la source, mets-le dans `kicker` (section 5) et dis l'année dans `say` si elle aide à suivre.
- Dernière scène : la réponse à la question de l'accroche, en une phrase claire. Pas une ouverture vague.
- `title` : le titre de la vidéo, affiché en haut de l'écran pendant toute la vidéo, 40 caractères au plus (espaces compris).
- Suis l'ordre de la vidéo source. Chaque scène a un `src` : le `[mm:ss]` du paragraphe qui la justifie.
- N'écris que ce que dit la source. Aucun fait, chiffre, nom ou date ajouté.
- La transcription est automatique : les noms propres y sont parfois mal écrits. Écris un nom seulement si tu reconnais la personne ou le lieu avec certitude, avec sa bonne orthographe. Sinon, désigne-la par son rôle ("le président de l'époque").
- N'utilise jamais un passage de sponsor, de promotion, d'appel à s'abonner ou de vie de la chaîne. Les lignes `[passage sponsorisé a à b, ignoré]` et `[passage probablement sponsorisé a à b, ignoré]` remplacent ces passages : n'utilise aucun minutage compris entre a et b (ni `src`, ni citation, ni `sfx`).
- Ne nomme jamais une marque ou un produit que la vidéo est payée pour promouvoir.
- N'écris jamais le nom de la ligne `Chaîne :`, ni celui de la personne qui anime la chaîne : ni dans `title`, ni dans `hook`, ni dans `say`, ni dans les `props`, ni dans une citation (`quote`, `props.text`) : si l'extrait le prononce, choisis un autre extrait. Le sujet et les mots de la ligne `Titre :` sont libres : tu peux les reprendre.

## 3. L'accroche (`hook`)

Même format à chaque fois : une phrase de 6 à 10 mots, 60 caractères au plus (espaces compris), en général une question, qui donne envie de connaître la réponse. La phrase s'adapte au sujet. "Dis-moi pourquoi..." est la formule par défaut quand elle colle. Autres formules : "Pourquoi... ?", "Tu sais ce qui se passe quand... ?", "Et si... ?", "Personne ne t'explique que...". En anglais : "Tell me why...?", "Why...?". L'accroche doit être vraie et la vidéo doit y répondre. Aucun chiffre qui n'est pas dans la source. Avec plusieurs parties, ne reprends pas la même formule deux parties de suite. Histoire, fait divers, horreur ou biographie : l'accroche n'est pas une question mais « Voici l'histoire de... » ou une phrase choc complète (« Il a fait croire à tout un pays qu'il était innocent »).
La couverture coupe l'accroche au premier « , » ou « : » : ce qui précède en gros titre, le reste sur une bande noire dessous. Pour une histoire, mets le sujet avant la coupure (« L'histoire de Marvin Gaye, partie 1 : de l'église à Motown ») ; sans coupure, l'accroche entière fait le titre. Le dessin de la couverture est la photo de la première person-card avec photo, sinon le buste de la première person-card, sinon le premier picto non drapeau des 3 premières scènes : mets-y un dessin du sujet global (globe, pièces).

Bonnes accroches :
- "Dis-moi pourquoi le ciel est bleu et pas violet ?"
- "Dis-moi pourquoi tu oublies ce que tu viens de lire ?"
- "Pourquoi les avions ne volent pas en ligne droite ?"
- "Tu sais ce qui se passe quand tu retiens ton souffle ?"
- "Et si le pain rassis n'était pas sec ?"
- "Personne ne t'explique pourquoi la mer est salée."

Mauvaises accroches :
- "Dis-moi pourquoi 97 % des gens se trompent ?" : chiffre inventé.
- "Le secret incroyable que personne ne veut te dire !" : promesse vide, aucun sujet.
- "Dans cette vidéo, nous allons parler de la lumière et de ses propriétés." : pas de question, trop long.

Question au spectateur (`question`, obligatoire) : chaque partie finit par une question courte posée au spectateur, juste avant l'appel à s'abonner que le code ajoute. Elle porte sur le sujet et parle de lui, pour donner envie de répondre en commentaire. 60 caractères au plus, finit par « ? ». Exemples : "Et toi, dans quelle position tu dors ?", "Et toi, tu relis tes cours ou tu les oublies ?". Pas de question générale ("Ça t'a plu ?") ni de quiz dont la réponse est dans la vidéo. Quand la question demande son avis, commence-la par « Pour toi, » (« Pour toi, quel pays aurait pu dominer à sa place ? ») ; garde « Et toi, » pour une question sur ses habitudes.

## 4. Écrire pour la voix

Le texte de `say` est lu par une voix de synthèse. Écris comme on parle.
- Un `say` = 1 ou 2 phrases courtes, 9 à 13 mots, 20 au plus. Une phrase = 15 mots au plus. Une idée qui demande plus de mots se coupe en deux scènes qui se suivent, avec chacune son visuel.
- Nombres : écris-les en chiffres dans `say` comme à l'écran ("en 2001", "3 000 personnes", "8 %", "1,3 milliard", "le 51e") : le code les fait dire en toutes lettres à la voix. Seules les fractions s'écrivent en lettres ("un tiers", "la moitié").
- Santé, argent, droit : garde les nuances de la source ("souvent", "peut", "chez certains"). N'écris jamais un conseil comme une certitude ni une promesse de guérison, et laisse de côté une affirmation forte que la source ne justifie pas. Explique le mécanisme, laisse le spectateur choisir.
- Sujets graves (morts, attentat, guerre, maladie, fait divers, horreur, catastrophe) : ton sobre et grave du début à la fin, jamais joyeux, aucune formule légère. Pas de `counter` pour compter des victimes, pas de `mascot` en pose `content` ou `surprise`, pas de `sfx`. Prends `key-title`, `stamp` ou `timeline`.
- Dans `say` seulement : pas de parenthèses, pas d'abréviations d'unités ("nanomètres", pas "nm") ; les sigles connus se gardent ("OTAN", "BRICS", "ONU"), pas de symboles (%, €, &, /). Les textes à l'écran (`props`) peuvent en avoir.
- Phrases complètes avec un verbe précis : « ses empereurs protègent leur frontière nord des peuples des steppes », pas « préfèrent garder leur frontière nord ».
- Pas de longue énumération lue à voix haute : trois éléments au plus, les deux derniers reliés par « et » (« la variole, la rougeole et la grippe »).
- En français, tutoie le spectateur.
- Jamais de tiret cadratin. Utilise une virgule, deux-points ou un point.
- Le `say` d'une scène `quote` présente la citation sans la répéter : la vraie voix de la source est jouée juste après.

### Écrire avec tes mots (anti-plagiat)

La vidéo raconte les mêmes faits que la source, pas avec les mêmes phrases.
- Ne recopie pas les phrases de la transcription. Garde les chiffres, les dates, les noms et les faits, change les mots et la construction : « En moyenne, on change de position entre 10 et 40 fois par nuit » devient « Chaque nuit, ton corps bouge 10 à 40 fois sans que tu le saches ».
- Ne suis pas la source phrase par phrase. Regroupe deux idées dans une scène, coupe les détails, change l'ordre quand le sens le permet. Ton rythme n'est pas celui de la source.
- `check` refuse une suite de 10 mots identiques à la source dans `say`, `hook` ou `question`, et une partie dont plus de 20 % du texte reprend des suites de 5 mots de la source. Une liste de lieux, un nom propre long ou une date restent possibles quand le reste de la phrase est à toi.
- Seule la citation (`quote`, `props.text`) reprend la source mot pour mot.

### Écrire sans tics d'IA (filtre anti-slop)

Le spectateur repère vite un texte écrit par une IA. Dans `hook`, `say` et les textes à l'écran :
- Aucun tiret long (cadratin ou demi-cadratin) ni double trait (`--`), aucun trait d'union isolé entre deux espaces. Remplace par un point, une virgule ou deux-points. Les traits d'union des mots composés restent (« États-Unis », « quatre-vingt-dix »).
- Pas de mots creux qui veulent impressionner : « révolutionnaire », « incroyable », « fascinant », « véritable », « crucial », « essentiel », « au cœur de », « un monde où », « une nouvelle ère », « changer la donne ». Dis le fait précis.
- Pas d'annonce de ce que tu vas dire : « Plongeons », « Voyons ensemble », « Dans cette vidéo », « Tu vas voir que ». Dis-le directement.
- Pas de fausse confidence : « Honnêtement », « Soyons clairs », « Spoiler », « Le truc, c'est que ».
- Pas de formule « Ce n'est pas X, c'est Y », « Non seulement X, mais aussi Y » plus d'une fois par vidéo.
- Pas de suite de phrases de trois mots pour faire un effet. Une phrase courte pour appuyer, oui ; trois de suite, non.
- Pas de liste forcée à trois éléments : autant d'éléments que la source en donne.
- Pas de conclusion vague : « L'avenir nous le dira », « Une chose est sûre », « À méditer ». Finis sur la réponse concrète.
- Pas de majuscules pour crier dans `say`, pas de guillemets pour souligner.
- Un sujet qui agit : « les chercheurs ont mesuré », pas « il a été montré ».

## 5. Les 16 types de scène

Recopie les noms de props et de `el` exactement : `check` refuse une prop inconnue, une prop manquante, une liste trop longue et un `el` qui n'existe pas. Les props marquées * sont obligatoires. Les autres sont facultatives : omets-les si la source ne donne rien, n'invente pas de valeur. `counter.to`, `counter.from` et `shape-diagram.values` sont des nombres sans guillemets. Les textes à l'écran peuvent contenir des chiffres. Ils sont courts : chaque texte a un plafond en caractères, espaces compris, donné entre crochets dans le tableau (par exemple [28 caractères] : 28 caractères au plus). `check` refuse un texte plus long, car il serait coupé à l'écran. Dans `el`, remplace N par un numéro : `chips.0`, jamais `chips.N`.

| type | quand l'utiliser | props | `el` possibles |
|---|---|---|---|
| `key-title` | la phrase-clé d'une idée | `text`* [90 caractères], `accent` [40 caractères] (un mot ou une suite de mots recopiés de `text`, posés sur la bande de couleur) ; `kicker`, `picto` (voir sous le tableau) | `text`, `accent` |
| `person-card` | qui a dit ou fait quoi, avec son personnage en papier | `name`* [48 caractères], `role` [100 caractères], `picto` (le drapeau de son pays) ; apparence : `gender`, `age`, `job`, `hair`, `hair_color`, `facial`, `hat`, `glasses`, `outfit`, `skin` (voir sous le tableau) ; `photo` ; `kicker` (voir sous le tableau) | `avatar`, `name`, `role` |
| `fact-chips` | 2 à 6 faits courts qui s'ajoutent | `chips`* : liste de textes (6 max) [28 caractères chacun] ; `kicker`, `picto` (voir sous le tableau) | `chips.0` à `chips.5` |
| `stack-list` | étapes ou raisons qui s'accumulent | `items`* : liste de textes (5 max) [60 caractères chacun] ; `kicker`, `picto` (voir sous le tableau) | `items.0` à `items.4` |
| `counter` | un nombre qui monte | `to`* : le nombre d'arrivée, sans texte ; `from` : nombre de départ ; `label` [60 caractères] : ce qu'on compte ; `unit` [4 caractères] : l'unité écrite après le nombre ("%", "x", "km") ; `kicker`, `picto` (voir sous le tableau) | `to` (lance le compte), `label` |
| `timeline` | une chronologie | `marks`* : liste de `{at, label}` (5 max, `at` obligatoire) [`at` 12 caractères, `label` 48 caractères] ; `start`, `end` : textes [30 caractères] ; `kicker`, `picto` (voir sous le tableau) | `marks.0` à `marks.4` |
| `icon-grid` | des catégories, une famille | `cells`* : liste de `{shape, label}` (9 max, `label` obligatoire) [`label` 16 caractères], `shape` = `circle`, `square`, `triangle`, `diamond`, `arrow` ou `strip` ; `kicker` (voir sous le tableau) | `cells.0` à `cells.8` |
| `stamp` | une conclusion forte, une idée reçue démentie | `text`* [48 caractères] (affiché en majuscules) ; `kicker`, `picto` (voir sous le tableau) | `text` |
| `quote` | une phrase exacte de la source, avec sa vraie voix | `text`* [200 caractères] (citation exacte), `speaker` [32 caractères] (section 7) ; `kicker`, `picto` (voir sous le tableau) | `text`, `speaker` |
| `object-state` | un objet qui change d'état | `object`* = `screen`, `board`, `jar`, `door`, `scale` ou `phone` ; `states`* : liste de textes (6 max) [36 caractères chacun]. Le premier état est visible dès le début, chaque état suivant le remplace sur son mot. `screen` et `board` affichent le texte dans l'objet ; `jar` se remplit, `door` s'ouvre, `scale` penche, avec le texte en dessous ; `phone` (SMS, messages) empile chaque état en bulle ; `kicker` (voir sous le tableau) | `states.1` à `states.5` |
| `shape-diagram` | une comparaison de tailles ou de quantités | `values`* : nombres (8 max) ; `shape` = `circle`, `square`, `triangle` ou `bar` ; `labels` : textes [14 caractères chacun], exactement autant que `values` ; `unit` [8 caractères] : l'unité écrite après chaque valeur ("Md$", "%", "km") ; `kicker` (voir sous le tableau) | `values.0` à `values.7`, `labels.0` à `labels.7` |
| `mascot` | le personnage Ideo qui réagit : la question naïve du spectateur, un fait surprenant, l'élément suivant, la leçon à retenir | `bubble`* [80 caractères] : sa bulle ; `pose` = `question` (par défaut), `surprise`, `montre` ou `content` ; `kicker` (voir sous le tableau) | `bubble` |
| `versus` | deux camps, deux options ou deux époques face à face | `left`*, `right`* [24 caractères chacun] ; `left_picto`, `right_picto` : un dessin par camp ; `kicker` (voir sous le tableau) | `left`, `right` |
| `map` | où ça se passe : un pays, une région, une route entre des pays | `focus`* = `world`, `europe`, `africa`, `asia`, `north-america`, `south-america`, `middle-east`, `oceania` ou `arctic` ; `places`* : liste de `{code, label}` (6 max), `code` = code du pays à deux lettres comme pour les drapeaux, `label` [24 caractères] ; `route` : liste de 2 à 6 codes reliés dans l'ordre par un trait ; `kicker` | `places.0` à `places.5`, `route` |
| `body` | le corps humain : une posture, un geste, ce qui se passe dans un organe | `pose`* = `standing`, `sitting`, `walking`, `running`, `lying-back`, `lying-starfish`, `lying-side-left`, `lying-side-right`, `lying-fetal` ou `lying-stomach` ; `setting` = `none`, `bed`, `chair`, `desk` ou `outdoor` ; `marks` : liste de `{part, label}` (4 max), `part` = `head`, `brain`, `neck`, `throat`, `shoulders`, `chest`, `heart`, `lungs`, `stomach`, `back`, `spine`, `hips`, `arms`, `hands`, `knees`, `legs` ou `feet`, `label` [28 caractères] ; `tone` = `good` (bleu), `bad` (rouge) ou `neutral` ; `kicker` | `marks.0` à `marks.3` |
| `artwork` | une œuvre d'art citée (tableau, dessin, sculpture) ou le logo d'une marque citée | `title`* [48 caractères] : le titre de l'œuvre ou le nom de la marque ; `artist` [40 caractères] (laisse vide pour un logo) ; `kicker` | `title`, `artist` |

Deux props facultatives s'ajoutent aux types :
- `kicker` [28 caractères], sur TOUS les types : une petite étiquette visible dès la première image de la scène. Mets-y la date, le lieu ou le nom de l'acte ("1991", "11 septembre 2001", "Irak, 2003", "Acte 2 : les BRICS"). Ce n'est pas un `el` : ne le mets pas dans `items`.
- `picto`, sur `key-title`, `fact-chips`, `stack-list`, `counter`, `timeline`, `stamp` et `quote` : un dessin en papier découpé qui illustre la scène, visible dès la première image. Dans `icon-grid`, chaque cellule peut avoir son `picto` à la place de `shape`. Ce n'est pas un `el`.

Personnages (`person-card`) : compose l'apparence de la personne avec ces props, toutes facultatives, d'après ce qui la rend reconnaissable. Ne mets que ce dont tu es sûr, mais jamais aucune prop. Deux personnes différentes n'ont jamais la même apparence.
- `gender` : `woman`, `man` ; `age` : `child`, `adult`, `old` ; `job` : `police`, `firefighter`, `doctor`, `judge`, `soldier`, `worker`, `journalist`, `lawyer` (donne la tenue et le couvre-chef)
- `hair` : `none`, `short`, `side`, `long`, `curly`, `wild`, `bun`, `crown-bald` ; `hair_color` : `black`, `brown`, `blond`, `red`, `grey`, `white`
- `facial` : `none`, `moustache`, `beard`, `goatee`, `sideburns` ; `glasses` : `true` ou `false`
- `hat` : `none`, `cap`, `kepi`, `bicorne`, `crown`, `helmet`, `top-hat`, `beret`, `turban`, `laurel`, `wig`
- `outfit` : `suit`, `uniform`, `robe`, `lab-coat`, `casual`, `toga`, `armor`, `dress` ; `skin` : `light`, `tan`, `brown`, `dark`
Exemple : un savant aux cheveux blancs en bataille donne `"hair": "wild", "hair_color": "white", "facial": "moustache", "outfit": "lab-coat"`. Dans une biographie ou une histoire, la personne principale est présentée une seule fois sur une `person-card` (pas une carte par acte) : ne répète ni son nom ni sa photo, et garde la même apparence si une autre carte la montre. Personne historique connue (savant, chef d'État, artiste), en biographie ou non, jamais fait divers ni personne privée : lance `ideo photo JOB "<nom>"` une fois par personne avant d'écrire le plan. Pour chaque réponse qui n'est pas « aucune photo libre », mets `"photo": true` sur les cartes de cette personne (le `name` de la carte reprend son nom), sinon garde le portrait en papier. Œuvre citée (le tableau d'un peintre) : lance aussi `ideo photo JOB "<titre>"` et n'écris la scène `artwork` que si l'image est trouvée, avec ce titre dans `title`. Marque citée : même scène `artwork`, lance `ideo photo JOB "<marque>"` et mets son nom dans `title` sans `artist`.

Drapeaux : partout où un `picto` est accepté, tu peux écrire `flag:` suivi du code du pays à deux lettres en minuscules : `flag:us`, `flag:cn`, `flag:ru`, `flag:in`, `flag:br`, `flag:za`, `flag:fr`, `flag:gb`, `flag:de`, `flag:jp`. Aussi `flag:eu` (Union européenne), `flag:un` (ONU) et `flag:su` (Union soviétique). Tous les pays ont leur drapeau, même s'ils ne sont pas dans ces exemples : écris leur code (`flag:iq` pour l'Irak, `flag:eg` pour l'Égypte). Pour une région, écris `flag:gb-sct` (Écosse), `flag:gb-eng` (Angleterre), `flag:gb-wls` (pays de Galles), `flag:gb-nir` (Irlande du Nord) ou `flag:es-ct` (Catalogne), pas le drapeau du pays voisin. Ne demande jamais un drapeau de pays dans `wishes`. Dès qu'un pays est nommé à l'écran, montre son drapeau. Quand un `say` cite trois pays ou plus (une alliance, un groupe, des pays visés), la scène est une `icon-grid` avec un drapeau et le nom du pays par cellule. Un `versus` entre deux pays a un drapeau de chaque côté.

Si aucun dessin de la liste ne montre ce dont parle une scène, ne mets pas de `picto` approximatif. Note ce qui t'a manqué dans un champ `"wishes"` au premier niveau du plan, à côté de `"parts"` : une liste de 0 à 5 textes courts [40 caractères], par exemple `"wishes": ["drapeau américain", "carte du monde"]`. Ces dessins seront ajoutés plus tard.

Humeur : pour un fait divers, un crime, une horreur ou une catastrophe, ajoute `"mood": "dark"` au premier niveau du plan, à côté de `"parts"` : fonds et papiers deviennent sombres. Sinon, n'écris rien. Le ton reste grave du début à la fin, jamais joyeux : pas de mascotte contente ni de formule légère, même après un moment positif de l'histoire.

Matière : ajoute `"paper"` au premier niveau du plan, à côté de `"parts"` : `"kraft"` (argent, économie), `"journal"` (histoire, politique, fait divers, horreur), `"millimetre"` (science, santé), `"album"` (biographie, histoire d'une personne). Sinon n'écris rien. Les supports de chaque scène (ticket, coupure de journal, post-it) sont choisis par le code.

Ton : ajoute `"ton": "pose"` au premier niveau du plan pour une biographie, une histoire, un fait divers ou un sujet grave : la version finale prend alors la voix posée. Sinon n'écris rien (voix dynamique).

Collages : dès qu'une personne connue est citée, lance `ideo photo` et montre sa photo sur sa `person-card`, sauf dans un fait divers ou pour une personne privée.

Valeurs de `picto` (recopie le nom exact) : `globe`, `flag`, `pin`, `city`, `house`, `factory`, `bank`, `coin`, `chart-up`, `chart-down`, `ship`, `plane`, `train`, `rocket`, `satellite`, `tank`, `shield`, `sword`, `bomb`, `dove`, `handshake`, `justice`, `wall`, `chain`, `lock`, `key`, `crown`, `ballot`, `megaphone`, `newspaper`, `tv`, `phone`, `computer`, `chip`, `book`, `brain`, `heart`, `eye`, `clock`, `calendar`, `lightbulb`, `atom`, `flask`, `leaf`, `sun`, `drop`, `fire`, `lightning`, `mountain`, `barrel`, `gear`, `people`, `lungs`, `stomach`, `spine`, `bone`, `muscle`, `tooth`, `blood`, `pill`, `syringe`, `virus`, `bed`, `pillow`, `moon`, `thermometer`, `scale-weight`, `apple`, `dumbbell`, `running-shoe`, `stethoscope`, `hospital`, `raised-bed`, `stomach-sleeper`, `knee-pillow`, `snore`, `pelvis-tilt`, `numb-arm`, `blood-stain`, `chalk-outline`, `crime-tape`, `handcuffs`, `knife`, `coffin`, `tombstone`, `mirror`, `mars`, `music-note`, `vinyl`, `microphone`, `ankle-monitor`, `hemicycle`, `credit-rating`, `constitution`. Un même picto revient au plus 2 fois par vidéo.

Détails :
- `shape-diagram` : la taille de chaque forme suit sa valeur. `bar` dessine des barres et écrit la valeur au-dessus de chacune, suivie de `unit` : donne toujours `unit` quand la valeur en a une.
- `counter` : `from` est le nombre affiché au départ du compte (0 si tu ne le mets pas), visible dès la première image. Ancre `to` sur un des premiers mots du `say` : le compte doit démarrer vite, pas à la fin de la phrase.
- Un écran doit apprendre quelque chose seul, sans le son : pas de liste de noms nus. Chaque texte d'une liste (`chips`, `items`, `label` d'une cellule) dit un fait complet, avec un chiffre ou un verbe : "8 % dorment sur le dos", pas "Sur le dos". "Russie", "Inde", "Chine" n'apprend rien ; "BRICS, créés en 2011" avec un `picto` apprend quelque chose.
- `mascot` : choisis `pose` selon la bulle. `question` : la question naïve du spectateur. `surprise` : un fait qui va contre l'intuition. `montre` : il désigne ce qui vient ensuite. `content` : la leçon à retenir.

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
```

## 6. `items[].on` : quand un élément apparaît

- Chaque élément du visuel apparaît sur le mot indiqué dans `on`. Un élément absent de `items` est visible dès la première image. Liste tous les éléments sauf `states.0` (visible dès le début) et `speaker` quand il est vide.
- `on` = un mot ou une courte suite de mots recopiés exactement du `say` de la même scène, là où l'élément doit apparaître.
- Mets les `items` dans l'ordre où leurs mots sont dits. Deux éléments peuvent partager le même mot.
- Répartis les éléments sur toute la durée du `say` : le dernier s'ancre sur un mot de la dernière phrase, sinon l'écran reste figé pendant que la voix continue.
- Pour tous les types : ancre le premier élément sur un des premiers mots du `say`. Le code le fait de toute façon apparaître au début de la scène, pour que l'écran ne reste jamais vide.

## 7. Citations et sons

- Une scène `quote` joue la vraie voix de la source. `props.text` = des mots recopiés exactement, dans l'ordre, d'un seul paragraphe de la transcription. Seule correction permise : recolle les apostrophes et les traits d'union ("c 'est" s'écrit "c'est", "est -il" s'écrit "est-il"). 8 secondes au plus, soit environ 20 mots : `check` refuse un extrait plus long. Jamais traduite.
- `src` de la citation = le `[mm:ss]` du paragraphe qui la contient.
- `speaker` = qui on entend dans l'extrait, comme la transcription le dit : "Prénom Nom", "Prénom Nom, média" ou le média seul. Les vidéos insèrent souvent des extraits d'ailleurs (journal télé, interview, discours) : l'indice est dans le texte autour ("comme l'a dit X", "sur telle antenne", "écoutez").
- Si la transcription ne dit pas qui parle, ou parle seulement d'"un journal" ou d'"un reportage" sans nommer le média, mets `"speaker": ""`. Pas de crédit vaut mieux qu'un faux crédit. `speaker` n'est jamais le nom de la chaîne YouTube, ni le titre de la vidéo, ni un nom inventé.
- Bon : le texte dit "comme l'expliquait Hubert Reeves sur France Inter" donne `"speaker": "Hubert Reeves, France Inter"`. Mauvais : `"speaker"` = le nom de la ligne `Chaîne :` de la transcription. Mauvais aussi : le nom du présentateur de la vidéo ("je suis Léa"). Une `quote` n'est jamais le présentateur qui lit un texte (lettre, article) : un extrait où la source passe la voix à quelqu'un d'autre, sinon mets le texte dans un `stamp` ou dans le `say`.
- Une ligne `[son 2:43 2.5s]` est un son de la vidéo source, sans parole. Pour le jouer après le `say` d'une scène, ajoute `"sfx": "2:43"` à cette scène (recopie le minutage qui suit `son`). Zéro à deux sons par vidéo (trois au plus pour la biographie d'un artiste musical), 10 secondes au plus chacun, seulement si le `say` parle de ce moment, et jamais sur un sujet grave (section 4). Jamais de `sfx` sur une scène `quote` : la citation joue déjà la vraie voix.

Exemple : la transcription contient

```text
[1:55] J'ai demandé à une physicienne de l'atmosphère de le résumer en une phrase. Le ciel n'est pas peint en bleu, c'est de la lumière du soleil renvoyée vers nous. Voilà, c'est vraiment ça, rien de plus compliqué.
[2:33] On peut le vérifier chez soi. Prenez un verre d'eau, ajoutez quelques gouttes de lait, et éclairez-le avec une lampe de poche.
[son 2:43 2.5s]
```

La citation devient `"text": "Le ciel n'est pas peint en bleu, c'est de la lumière du soleil renvoyée vers nous"` avec `"src": "1:55"` et `"speaker": ""` (la transcription ne donne pas son nom), et la scène de l'expérience prend `"src": "2:33"` et `"sfx": "2:43"`.

## 8. Variété

Pour que la vidéo n'ait pas l'air générée :
- Jamais deux fois de suite le même type de scène.
- `key-title` : 1 fois par acte au plus. `mascot` : 4 fois au plus par vidéo, jamais deux de suite. `versus` : 2 fois au plus par vidéo.
- Au moins une scène sur deux montre un dessin : un `picto`, un `object-state`, un `versus`, un `shape-diagram`, un `timeline`, une `map`, un `body` ou la `mascot`. Choisis le `picto` qui montre la chose dont parle la scène, pas un symbole vague.
- Dès que le sujet touche au corps (santé, sommeil, sport, posture, organe) : des scènes `body`, avec la posture dont on parle et les zones concernées en `marks`. Dès qu'un lieu compte (un pays, un trajet, une frontière) : une `map`.
- Dès qu'il y a deux camps, deux époques ou un avant et un après : `versus` ou `object-state`. Dès qu'il y a trois dates ou plus : `timeline`. Dès qu'il y a deux nombres à comparer : `shape-diagram` avec `unit`.
- Une `quote` toutes les 8 à 10 scènes si la source contient des extraits nets (journal, discours, interview). Si elle n'en a qu'un, un seul suffit ; si elle n'en a pas, aucun.
- Varie les débuts de `say` : pas trois scènes de suite qui commencent par le même mot.

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

Chaque ligne commence par l'endroit ("Plan", "Partie 1", "Partie 1, scène 4") et dit quoi faire. Corrige seulement ce qu'elle nomme.

| l'erreur contient | ce qu'il faut faire |
|---|---|
| `n'est pas un JSON valide` | corrige la syntaxe (virgule, guillemet, accolade) à l'endroit indiqué |
| `version` | mets `"version": 1` |
| `langue` | mets dans `lang` la langue indiquée et écris les textes dans cette langue |
| `n'a pas de voix de synthèse` | ne corrige rien : montre l'erreur à l'utilisateur et arrête-toi |
| `parties au maximum` ou `au moins 1 partie` | entre 1 et 8 objets dans `parts` |
| `numéro « n »` | numérote les parties 1, 2, 3 dans l'ordre |
| `« title » est manquant ou vide` ou `« say » est manquant ou vide` | remplis ce champ |
| `l'accroche « hook »` | écris une accroche (section 3) |
| `la « question » au spectateur` | ajoute `question` à la partie (section 3) |
| `recopie la vidéo d'origine mot pour mot` | réécris ce champ avec tes mots et une autre construction, en gardant les chiffres et les faits (section 4) |
| `reprend des suites de 5 mots` | réécris les scènes les plus proches de la source : regroupe, coupe, change l'ordre (section 4) |
| `« scenes » doit être une liste` | mets au moins une scène dans la partie |
| `type inconnu` | prends un des 16 types de la section 5 |
| `prop inconnue` ou `manquante` | utilise seulement les props acceptées que l'erreur liste |
| `« props.X » doit être` | donne à cette prop le format indiqué (nombre, liste, valeur permise) |
| `« props.labels » a` | donne autant de `labels` que de `values` |
| `« props.accent »` | recopie dans `accent` un mot de `text` |
| `« el » ... invalide` | prends un des chemins acceptés que l'erreur liste |
| `contient le nom de la chaîne YouTube` | réécris ce champ sans ce nom ; pour `props.text` d'une `quote`, prends un autre extrait qui ne le dit pas |
| `« speaker » doit nommer` | vide `speaker` (`""`), ou mets la personne ou le média qu'on entend |
| `« props » doit être un objet` | écris `props` entre accolades |
| `« items » doit être une liste` | écris `items` entre crochets : `[{"el": ..., "on": ...}]` |
| `tiret cadratin` | remplace-le par une virgule, deux-points ou un point |
| `n'est pas dans le texte de « say »` | recopie dans `on` un mot exact du `say` de cette scène |
| `est dit avant l'item` | remets les items dans l'« Ordre attendu » donné |
| `chaque élément de « items »` | chaque item a `el` et un `on` non vide |
| `« src » est manquant` | ajoute le `[mm:ss]` du paragraphe source |
| `minutage invalide` | écris `mm:ss`, par exemple `"12:30"` |
| `dépasse la durée de la vidéo` | prends un minutage qui existe dans la transcription |
| `n'est pas dans sfx.json` | recopie un minutage d'une ligne `[son ...]` ou retire `sfx` |
| `« sfx » sur une scène « quote »` | retire `sfx` de la citation, ou mets-le sur une autre scène |
| `demande « props.text »` | mets la citation exacte dans `props.text` |
| `citation introuvable` | recopie la citation depuis le "passage le plus proche" donné, et mets son minutage dans `src` |
| `la citation dure` | garde seulement une partie des mots de la citation (8 s, environ 20 mots au plus) |
| `trop courte` | ajoute du texte `say` ou une scène, de la durée indiquée |
| `trop longue` | retire du texte ou des scènes, de la durée indiquée |
| `tient en une seule vidéo` | fusionne toutes les parties en une seule |
| `caractères, N au plus` | raccourcis ce texte à N caractères au plus ; pour `props.text` d'une `quote`, garde une partie des mots de la citation |
| `est dans un passage sponsorisé` | prends un autre passage, hors sponsor |
