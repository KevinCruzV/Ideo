# Guide d'écriture de plan.json

Lis ce guide une seule fois, en entier, avant d'écrire.

## 1. Le travail

Tu lis la transcription compacte d'une vidéo YouTube et tu écris `plan.json` : une vidéo verticale courte qui réexplique les idées principales, avec une voix off et des formes en papier découpé. Chaque scène a un texte dit à voix haute (`say`), un visuel (`type` + `props`) et des éléments qui apparaissent sur des mots du texte (`items`). Tout le reste (voix, minutage, rendu) est fait par le code.

Langue : mets dans `"lang"` la valeur de la ligne `Langue :` de la transcription, et écris TOUS les textes (`title`, `hook`, `say`, textes des `props`) dans cette langue. Ce guide est en français, la vidéo peut être en anglais : dans ce cas tout est en anglais.

## 2. Choisir

- Une seule vidéo (une seule partie dans `parts`). Plusieurs parties seulement si le contenu utile dépasse 5 minutes de voix off (environ 750 mots de `say`), 8 parties au maximum, chacune compréhensible seule.
- Garde les quelques idées qui comptent, pas tout. Une idée par scène.
- Une vidéo fait 8 à 25 scènes. Repère : 12 scènes d'environ 18 mots donnent environ 90 s.
- Durée estimée = mots de `hook` et de tous les `say` divisés par 2,6 (2,8 en anglais), plus 3 s de fin, plus la durée des extraits audio. Elle doit être entre 45 et 300 s.
- Suis l'ordre de la vidéo source. Chaque scène a un `src` : le `[mm:ss]` du paragraphe qui la justifie.
- N'écris que ce que dit la source. Aucun fait, chiffre, nom ou date ajouté.
- N'écris nulle part dans le plan le nom de la chaîne, celui de la personne qui a fait la vidéo, ni le titre de la vidéo (lignes `Chaîne :` et `Titre :`). Reformule le sujet avec tes mots.

## 3. L'accroche (`hook`)

Même format à chaque fois : une phrase de 6 à 10 mots, en général une question, qui donne envie de connaître la réponse. La phrase s'adapte au sujet. "Dis-moi pourquoi..." est la formule par défaut quand elle colle. Autres formules : "Pourquoi... ?", "Tu sais ce qui se passe quand... ?", "Et si... ?", "Personne ne t'explique que...". En anglais : "Tell me why...?", "Why...?". L'accroche doit être vraie et la vidéo doit y répondre. Aucun chiffre qui n'est pas dans la source. Avec plusieurs parties, ne reprends pas la même formule deux parties de suite.

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

## 4. Écrire pour la voix

Le texte de `say` est lu par une voix de synthèse. Écris comme on parle.
- Un `say` = 1 à 3 phrases courtes, 12 à 25 mots. Une phrase = 15 mots au plus.
- Nombres en lettres dans `say` : "quarante fois", pas "40 fois". Évite les dates dans `say`, mets-les dans les `props` à l'écran.
- Pas de parenthèses, pas d'abréviations ("nanomètres", pas "nm"), pas de symboles (%, €, &, /).
- Pas d'énumération lue à voix haute. Trois éléments au plus, chacun dans sa phrase.
- En français, tutoie le spectateur.
- Jamais de tiret cadratin. Utilise une virgule, deux-points ou un point.
- Le `say` d'une scène `quote` présente la citation sans la répéter : la vraie voix de la source est jouée juste après.

## 5. Les 12 types de scène

Recopie les noms de props et de `el` exactement : `check` refuse une prop inconnue, une prop manquante, une liste trop longue et un `el` qui n'existe pas. `counter.to`, `counter.from` et `shape-diagram.values` sont des nombres sans guillemets. Les textes à l'écran peuvent contenir des chiffres. Courts : 2 à 6 mots par étiquette.

| type | quand l'utiliser | props | `el` possibles |
|---|---|---|---|
| `key-title` | la phrase-clé d'une idée | `text`, `accent` (un mot de `text`, posé sur la bande de couleur) | `text`, `accent` |
| `person-card` | qui a dit ou fait quoi | `name`, `role` | `avatar`, `name`, `role` |
| `fact-chips` | 2 à 6 faits courts qui s'ajoutent | `chips` : liste de textes (6 max) | `chips.0` ... `chips.5` |
| `stack-list` | étapes ou raisons qui s'accumulent | `items` : liste de textes (5 max) | `items.0` ... `items.4` |
| `counter` | un nombre qui monte | `label`, `from`, `to` (nombres) | `to` (lance le compte), `label` |
| `timeline` | une chronologie | `start`, `end` (textes), `marks` : liste de `{at, label}` (5 max) | `marks.0` ... `marks.4` |
| `icon-grid` | des catégories, une famille | `cells` : liste de `{shape, label}` (9 max), `shape` = `circle`, `square`, `triangle`, `diamond`, `arrow` ou `strip` | `cells.0` ... `cells.8` |
| `stamp` | une conclusion forte, une idée reçue démentie | `text` (affiché en majuscules) | `text` |
| `quote` | une phrase exacte de la source, avec sa vraie voix | `text` (citation exacte), `speaker` (section 7) | `text`, `speaker` |
| `object-state` | un objet qui change d'état | `object` = `screen`, `board`, `jar`, `door` ou `scale` ; `states` : liste de textes (6 max) | `states.1` ... `states.5` |
| `shape-diagram` | une comparaison de tailles ou de quantités | `shape` = `circle`, `square`, `triangle` ou `bar` ; `values` : nombres (8 max) ; `labels` : textes, autant que `values` | `values.0` ..., `labels.0` ... |
| `mascot` | la question naïve du spectateur | `bubble` | `bubble` |

Détails :
- `object-state` : le premier état est visible dès le début, chaque `states.N` suivant le remplace sur son mot. `screen` et `board` affichent le texte de l'état dans l'objet ; `jar` se remplit, `door` s'ouvre, `scale` penche, avec le texte en dessous.
- `shape-diagram` : la taille de chaque forme suit sa valeur. `bar` dessine des barres.
- `counter` : `to` est un nombre, sans texte. L'unité va dans `label`.
- `mascot` : au plus une fois par vidéo (le personnage n'est pas encore dessiné).

Un exemple par type :

```json
{"type": "key-title", "say": "Ce que tu oublies le plus vite, c'est ce que tu n'as jamais révisé.", "props": {"text": "La courbe de l'oubli", "accent": "l'oubli"}, "items": [{"el": "text", "on": "oublies"}, {"el": "accent", "on": "révisé"}], "src": "0:12"}
{"type": "person-card", "say": "Le psychologue allemand Hermann Ebbinghaus a testé sa propre mémoire pendant des mois.", "props": {"name": "Hermann Ebbinghaus", "role": "Psychologue allemand, 1885"}, "items": [{"el": "avatar", "on": "psychologue"}, {"el": "name", "on": "Ebbinghaus"}, {"el": "role", "on": "mémoire"}], "src": "1:05"}
{"type": "fact-chips", "say": "Il apprenait des syllabes sans aucun sens, par listes de treize, jusqu'à les réciter sans erreur.", "props": {"chips": ["Syllabes sans sens", "Listes de 13", "Zéro erreur"]}, "items": [{"el": "chips.0", "on": "syllabes"}, {"el": "chips.1", "on": "listes"}, {"el": "chips.2", "on": "erreur"}], "src": "1:40"}
{"type": "stack-list", "say": "Révise juste avant d'oublier. Espace tes révisions. Et teste-toi au lieu de relire.", "props": {"items": ["Réviser avant d'oublier", "Espacer", "Se tester"]}, "items": [{"el": "items.0", "on": "Révise"}, {"el": "items.1", "on": "Espace"}, {"el": "items.2", "on": "teste-toi"}], "src": "6:10"}
{"type": "counter", "say": "Au total, il a appris plus de deux mille syllabes inventées.", "props": {"label": "syllabes apprises", "from": 0, "to": 2300}, "items": [{"el": "to", "on": "appris"}, {"el": "label", "on": "syllabes"}], "src": "2:02"}
{"type": "timeline", "say": "Son expérience date du dix-neuvième siècle, et des chercheurs l'ont refaite récemment avec le même résultat.", "props": {"start": "1880", "end": "2020", "marks": [{"at": "1885", "label": "Ebbinghaus publie"}, {"at": "2015", "label": "Expérience refaite"}]}, "items": [{"el": "marks.0", "on": "siècle"}, {"el": "marks.1", "on": "récemment"}], "src": "4:30"}
{"type": "icon-grid", "say": "Quatre choses aident la mémoire : le sommeil, la répétition, l'émotion et le sens.", "props": {"cells": [{"shape": "circle", "label": "Sommeil"}, {"shape": "square", "label": "Répétition"}, {"shape": "triangle", "label": "Émotion"}, {"shape": "diamond", "label": "Sens"}]}, "items": [{"el": "cells.0", "on": "sommeil"}, {"el": "cells.1", "on": "répétition"}, {"el": "cells.2", "on": "émotion"}, {"el": "cells.3", "on": "sens"}], "src": "5:15"}
{"type": "stamp", "say": "Relire ses notes la veille ne suffit pas. C'est même la méthode la moins efficace.", "props": {"text": "Relire ne suffit pas"}, "items": [{"el": "text", "on": "suffit"}], "src": "5:50"}
{"type": "quote", "say": "Une chercheuse interrogée sur France Culture le dit simplement.", "props": {"text": "on n'oublie pas par paresse, le cerveau fait du tri", "speaker": "France Culture"}, "items": [{"el": "text", "on": "dit"}, {"el": "speaker", "on": "simplement"}], "src": "3:12"}
{"type": "object-state", "say": "À chaque révision, le souvenir tient plus longtemps, et le bocal se remplit.", "props": {"object": "jar", "states": ["1re révision", "2e révision", "3e révision"]}, "items": [{"el": "states.1", "on": "souvenir"}, {"el": "states.2", "on": "remplit"}], "src": "6:40"}
{"type": "shape-diagram", "say": "Juste après la leçon, tu retiens tout. Un jour plus tard, il reste à peine un tiers.", "props": {"shape": "circle", "values": [1, 0.34], "labels": ["Juste après", "Un jour plus tard"]}, "items": [{"el": "values.0", "on": "leçon"}, {"el": "labels.0", "on": "retiens"}, {"el": "values.1", "on": "jour"}, {"el": "labels.1", "on": "tiers"}], "src": "2:30"}
{"type": "mascot", "say": "Alors, réviser la veille de l'examen, ça ne sert à rien ?", "props": {"bubble": "Et réviser la veille ?"}, "items": [{"el": "bubble", "on": "réviser"}], "src": "5:40"}
```

## 6. `items[].on` : quand un élément apparaît

- Chaque élément du visuel apparaît sur le mot indiqué dans `on`. Un élément absent de `items` est visible dès la première image : liste-les tous.
- `on` = un mot ou une courte suite de mots recopiés exactement du `say` de la même scène, là où l'élément doit apparaître.
- Choisis un mot, pas un nombre : la voix peut l'écrire autrement.
- Mets les `items` dans l'ordre où leurs mots sont dits.
- Le premier élément doit apparaître dans la première phrase du `say`, sinon l'écran reste vide (surtout `stamp`, `quote`, `key-title`).

## 7. Citations et sons

- Une scène `quote` joue la vraie voix de la source. `props.text` = des mots recopiés exactement, dans l'ordre, d'un seul paragraphe de la transcription. Seule correction permise : recolle les apostrophes et les traits d'union ("c 'est" s'écrit "c'est", "est -il" s'écrit "est-il"). Moins de 8 secondes : 20 mots au plus. Jamais traduite.
- `src` de la citation = le `[mm:ss]` du paragraphe qui la contient.
- `speaker` = qui on entend dans l'extrait, comme la transcription le dit : "Prénom Nom", "Prénom Nom, média" ou le média seul. Les vidéos insèrent souvent des extraits d'ailleurs (journal télé, interview, discours) : l'indice est dans le texte autour ("comme l'a dit X", "sur telle antenne", "écoutez").
- Si la transcription ne dit pas qui parle, mets `"speaker": ""`. Pas de crédit vaut mieux qu'un faux crédit. Jamais la chaîne YouTube, jamais le titre de la vidéo, jamais un nom inventé.
- Bon : le texte dit "comme l'expliquait Hubert Reeves sur France Inter" donne `"speaker": "Hubert Reeves, France Inter"`. Mauvais : `"speaker"` = le nom de la ligne `Chaîne :` de la transcription. Mauvais aussi : le nom du présentateur de la vidéo ("je suis Léa") : quand on entend le présentateur ou l'auteur de la vidéo, mets `"speaker": ""`.
- Une ligne `[son 2:43 2.5s]` est un son de la vidéo source, sans parole. Pour le jouer après le `say` d'une scène, ajoute `"sfx": "2:43"` à cette scène (recopie le minutage qui suit `son`). Zéro à deux sons par vidéo, seulement si le `say` parle de ce moment.

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
- `key-title` : 2 fois au plus par vidéo.
- Une `quote` ou un `object-state` toutes les 4 à 6 scènes.
- Varie les débuts de `say` : pas trois scènes de suite qui commencent par le même mot.

## 9. Exemple complet

Source : une vidéo française de 3 min 49 sur la couleur du ciel. Une vidéo de 12 scènes, environ 95 s.

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
      "scenes": [
        {
          "type": "key-title",
          "say": "La lumière du soleil est blanche. Pourtant, au-dessus de ta tête, le ciel est bleu.",
          "props": {"text": "Une lumière blanche, un ciel bleu", "accent": "bleu"},
          "items": [{"el": "text", "on": "blanche"}, {"el": "accent", "on": "bleu"}],
          "src": "0:02"
        },
        {
          "type": "shape-diagram",
          "say": "Cette lumière mélange toutes les couleurs, et chacune est une onde : longue pour le rouge, courte pour le violet.",
          "props": {"shape": "bar", "values": [700, 400], "labels": ["rouge, 700 nm", "violet, 400 nm"]},
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
          "say": "Dans l'air, cette lumière croise des milliards de molécules d'azote et d'oxygène, bien plus petites que ces ondes.",
          "props": {"chips": ["Des milliards de molécules", "Azote et oxygène", "Plus petites que l'onde"]},
          "items": [
            {"el": "chips.0", "on": "milliards"},
            {"el": "chips.1", "on": "azote"},
            {"el": "chips.2", "on": "petites"}
          ],
          "src": "0:49"
        },
        {
          "type": "counter",
          "say": "Elles renvoient la lumière partout. Et plus l'onde est courte, plus elle rebondit : le bleu, plus de cinq fois plus que le rouge.",
          "props": {"label": "fois plus de bleu renvoyé", "from": 1, "to": 5},
          "items": [{"el": "to", "on": "bleu"}, {"el": "label", "on": "rouge"}],
          "src": "1:11"
        },
        {
          "type": "person-card",
          "say": "Ce phénomène porte le nom du physicien anglais Lord Rayleigh, qui l'a mis en équation au dix-neuvième siècle.",
          "props": {"name": "Lord Rayleigh", "role": "Physicien anglais, 1871"},
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
          "props": {"items": ["Le soleil envoie moins de violet", "L'atmosphère en absorbe", "Nos yeux préfèrent le bleu"]},
          "items": [
            {"el": "items.0", "on": "soleil"},
            {"el": "items.1", "on": "absorbe"},
            {"el": "items.2", "on": "yeux"}
          ],
          "src": "2:11"
        },
        {
          "type": "object-state",
          "say": "Tu peux le voir chez toi : un verre d'eau, quelques gouttes de lait, une lampe. De côté, l'eau devient bleutée.",
          "props": {"object": "jar", "states": ["Eau et lait", "Vu de côté : bleuté"]},
          "items": [{"el": "states.1", "on": "bleutée"}],
          "sfx": "2:43",
          "src": "2:33"
        },
        {
          "type": "shape-diagram",
          "say": "Le soir, la lumière traverse jusqu'à quarante fois plus d'air qu'à midi. Le bleu se perd en route, il reste le rouge.",
          "props": {"shape": "square", "values": [1, 40], "labels": ["midi", "soir"]},
          "items": [
            {"el": "values.0", "on": "midi"},
            {"el": "values.1", "on": "soir"},
            {"el": "labels.0", "on": "midi"},
            {"el": "labels.1", "on": "rouge"}
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
          "props": {"cells": [{"shape": "circle", "label": "Mars"}, {"shape": "square", "label": "Jour : caramel"}, {"shape": "diamond", "label": "Soir : bleu"}]},
          "items": [
            {"el": "cells.0", "on": "Mars"},
            {"el": "cells.1", "on": "caramel"},
            {"el": "cells.2", "on": "coucher"}
          ],
          "src": "3:33"
        }
      ]
    }
  ]
}
```

Avec plusieurs parties : ajoute des objets dans `parts` avec `"n": 2`, `"n": 3`, chacun avec son `title`, son `hook` et ses `scenes`.

## 10. Erreurs de `check`

Chaque ligne commence par l'endroit ("Plan", "Partie 1", "Partie 1, scène 4") et dit quoi faire. Corrige seulement ce qu'elle nomme.

| l'erreur contient | ce qu'il faut faire |
|---|---|
| `n'est pas un JSON valide` | corrige la syntaxe (virgule, guillemet, accolade) à l'endroit indiqué |
| `version` | mets `"version": 1` |
| `langue` | mets dans `lang` la langue indiquée et écris les textes dans cette langue |
| `parties au maximum` ou `au moins 1 partie` | entre 1 et 8 objets dans `parts` |
| `numéro « n »` | numérote les parties 1, 2, 3 dans l'ordre |
| `est manquant ou vide` | remplis le champ nommé (`title`, `say`) |
| `l'accroche « hook »` | écris une accroche (section 3) |
| `« scenes » doit être une liste` | mets au moins une scène dans la partie |
| `type inconnu` | prends un des 12 types de la section 5 |
| `prop inconnue` ou `manquante` | utilise seulement les props acceptées que l'erreur liste |
| `« props.X » doit être` | donne à cette prop le format indiqué (nombre, liste, valeur permise) |
| `« el » ... invalide` | prends un des chemins acceptés que l'erreur liste |
| `contient le nom de la chaîne` ou `le titre de la vidéo source` | reformule ce champ sans ce nom ni ce titre |
| `« props » doit être un objet` | écris `props` entre accolades |
| `tiret cadratin` | remplace-le par une virgule, deux-points ou un point |
| `n'est pas dans le texte de « say »` | recopie dans `on` un mot exact du `say` de cette scène |
| `chaque élément de « items »` | chaque item a `el` et un `on` non vide |
| `« src » est manquant` | ajoute le `[mm:ss]` du paragraphe source |
| `minutage invalide` | écris `mm:ss`, par exemple `"12:30"` |
| `dépasse la durée de la vidéo` | prends un minutage qui existe dans la transcription |
| `n'est pas dans sfx.json` | recopie un minutage d'une ligne `[son ...]` ou retire `sfx` |
| `demande « props.text »` | mets la citation exacte dans `props.text` |
| `citation introuvable` | recopie la citation depuis le "passage le plus proche" donné, et mets son minutage dans `src` |
| `trop courte` | ajoute du texte `say` ou une scène, de la durée indiquée |
| `trop longue` | retire du texte ou des scènes, de la durée indiquée |
| `tient en une seule vidéo` | fusionne toutes les parties en une seule |
