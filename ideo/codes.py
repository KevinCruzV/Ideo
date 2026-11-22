import re

ERROR_PATTERNS = (
    ("wishes-invalides", r"« wishes"),
    ("type-inconnu", r"type inconnu"),
    ("texte-trop-long", r"caractères, \d+ au plus"),
    ("drapeau-inconnu", r"n'est pas un drapeau connu"),
    ("props-invalides", r"prop inconnue|prop « \w+ » manquante|« props\.[\w.]+ » doit être|« props\.labels »|« props\.accent »"),
    ("el-invalide", r"« el » « |« items » doit|chaque élément de « items »"),
    ("items-desordre", r"est dit avant l'item"),
    ("ancre-absente", r"n'est pas dans le texte de « say »"),
    ("citation-introuvable", r"citation introuvable|la citation « .* » est introuvable|« props\.text », la citation exacte"),
    ("citation-trop-longue", r"la citation dure"),
    ("source-fin-video", r"dans la fin de la vidéo"),
    ("source-sponsorisee", r"passage sponsorisé"),
    ("nom-de-chaine", r"nom de la chaîne YouTube|« speaker » doit nommer"),
    ("tiret-cadratin", r"tiret cadratin"),
    ("break-invalide", r"« break »"),
    ("sfx-invalide", r"« sfx »|le son \S+ n'est pas dans sfx\.json|le son source"),
    ("src-invalide", r"« src »|minutage invalide"),
    ("plan-trop-court", r"trop courte"),
    ("plan-trop-long", r"trop longue"),
    ("parties-fusionnables", r"tient en une seule vidéo"),
    ("trop-de-scenes", r"scènes, \d+ au plus par vidéo"),
)
COMPILED = tuple((code, re.compile(pattern)) for code, pattern in ERROR_PATTERNS)
DEFAULT_ERROR = "plan-invalide"

LESSONS = {
    "annee-sans-kicker": "Dès qu'un say donne une année, mets cette date dans le kicker de la scène.",
    "rythme-hache": "Vise 4 à 6 scènes par minute : fusionne les scènes courtes et développe chaque idée avant la suivante.",
    "survol": "Ne survole pas la source : garde moins de sujets et explique bien chacun, une vidéo courte convient.",
    "peu-de-dessins": "Mets un picto ou un dessin (object-state, versus, shape-diagram, timeline, mascot) sur au moins une scène sur deux.",
    "liste-nue": "N'écris jamais une liste de simples noms : ajoute un chiffre ou un détail à chaque entrée, ou prends un dessin.",
    "barres-sans-unite": "Donne toujours un unit à un shape-diagram en barres, par exemple Md$ ou %.",
    "compteur-sujet-grave": "Pas de compteur animé pour des morts ou un drame : prends un stamp ou un key-title sobre.",
    "compteur-sans-unite": "Quand le say parle de pourcentage, mets unit sur le counter, par exemple %.",
    "fin-en-question": "Finis la vidéo par la réponse à l'accroche, jamais par une question.",
    "meme-type-suite": "Ne mets pas deux scènes du même type de suite : alterne les types.",
    "trop-de-mascot": "Garde 4 scènes mascot au plus par vidéo.",
    "trop-de-key-title": "Garde au plus un key-title toutes les 6 scènes.",
    "trop-de-versus": "Garde 3 scènes versus au plus par vidéo.",
    "say-trop-long": "Coupe tout say de plus de 30 mots en deux scènes.",
    "say-trop-court": "Donne au moins 8 mots à chaque say : fusionne les scènes trop courtes avec leurs voisines.",
    "sans-kicker": "Mets un kicker (date, lieu ou acte) sur les scènes qui changent de moment ou de lieu.",
    "debuts-identiques": "Varie le premier mot de trois say qui se suivent.",
    "items-groupes-debut": "Ancre le dernier item d'une scène sur un mot de la dernière phrase du say, pas tous au début.",
    "premier-element-tardif": "Ancre le premier item sur un mot du début du say, ou ajoute un kicker ou un picto.",
    "duree-hors-cible": "Reste sous 300 s par vidéo : coupe des scènes ou découpe en plusieurs parties.",
    "citation-introuvable": "Recopie une citation mot pour mot depuis la transcription, à moins de 90 s de son src.",
    "citation-trop-longue": "Choisis une citation de 8 secondes au plus.",
    "ancre-absente": "Recopie chaque on tel qu'il apparaît dans le say, mot pour mot.",
    "items-desordre": "Classe les items dans l'ordre où leurs mots sont dits dans le say.",
    "texte-trop-long": "Respecte le plafond de caractères de chaque texte à l'écran, sinon il est coupé.",
    "props-invalides": "Utilise seulement les props du guide pour chaque type de scène, avec les bons types de valeurs.",
    "type-inconnu": "Choisis le type de chaque scène dans la liste du guide.",
    "el-invalide": "Utilise pour el un chemin accepté par le type de scène, avec un numéro, jamais N.",
    "plan-trop-court": "Écris au moins 45 s de vidéo : développe les say ou ajoute des scènes.",
    "plan-trop-long": "Reste sous 300 s par vidéo : coupe des scènes ou découpe en plusieurs parties.",
    "parties-fusionnables": "Fusionne les parties si le tout tient en moins de 300 s.",
    "trop-de-scenes": "Garde 45 scènes au plus par vidéo.",
    "source-sponsorisee": "Choisis des src hors des passages sponsorisés.",
    "source-fin-video": "N'utilise pas la fin de la source (remerciements, abonnement) pour une scène.",
    "nom-de-chaine": "Ne nomme jamais la chaîne ni son animateur, ni dans un texte ni dans un speaker.",
    "tiret-cadratin": "N'écris aucun tiret cadratin : utilise une virgule, deux-points ou un point.",
    "src-invalide": "Écris chaque src en mm:ss, recopié d'un paragraphe de la transcription.",
    "sfx-invalide": "Prends un sfx dans sfx.json, jamais sur une scène quote.",
    "sans-pause-d-acte": "Dans une vidéo de plus de 10 scènes, mets \"break\": true sur la première scène de chaque nouvel acte.",
    "break-invalide": "Écris break comme un booléen, true ou false, jamais comme un texte.",
    "pays-sans-drapeau": "Mets flag:<code> sur chaque nom de pays affiché seul, par exemple flag:cn pour la Chine, dans une icon-grid, un versus ou une liste.",
    "scene-trop-chargee": "Coupe en deux scènes une liste de 5 éléments ou plus aux textes longs : le texte doit rester lisible sur téléphone.",
    "pays-cites-sans-drapeaux": "Quand un say cite 3 pays ou plus, montre leurs drapeaux avec une icon-grid : une cellule par pays, picto flag:<code>.",
    "route-sans-carte": "Quand un say décrit une route ou un trajet entre des pays, fais une scène map avec route : [codes des pays].",
    "corps-sans-dessin": "Quand une vidéo parle du corps ou d'une posture, fais une scène body avec pose et marks sur les zones citées.",
    "ia-tiret": "N'écris aucun tiret long, double trait ou trait isolé : un point, une virgule ou deux-points.",
    "ia-mots-creux": "Évite les mots creux (incroyable, essentiel, révolutionnaire, au cœur de) : dis le fait précis.",
    "ia-annonce": "N'annonce pas ce que tu vas dire (plongeons, voyons ensemble, dans cette vidéo) : dis-le directement.",
    "ia-fausse-confidence": "Pas de fausse confidence (honnêtement, soyons clairs, spoiler) : dis le fait.",
    "ia-formule-binaire": "Pas plus d'une formule « ce n'est pas X, c'est Y » ou « non seulement X, mais » par vidéo.",
    "ia-phrases-courtes": "Pas trois phrases de trois mots ou moins de suite : regroupe-les, une seule phrase courte pour appuyer.",
    "ia-conclusion-vague": "Finis sur la réponse concrète, jamais sur une conclusion vague (l'avenir nous le dira, une chose est sûre).",
    "ia-majuscules": "N'écris pas de mot en majuscules dans un say, sauf un sigle courant (OTAN, BRICS, ONU).",
    "ia-guillemets": "N'utilise pas de guillemets dans un say : ils sont réservés à la scène quote.",
    "drapeau-existe": "Avant de noter un drapeau dans wishes, cherche flag:<code> : les drapeaux de pays existent tous.",
    "drapeau-inconnu": "Écris flag: suivi du code de pays à deux lettres en minuscules, par exemple flag:fr.",
    "wishes-invalides": "Garde wishes à 5 textes de 40 caractères au plus.",
    "plan-invalide": "Relis le message de check et corrige exactement ce qu'il demande avant de relancer.",
}
CODE_ONLY = frozenset({
    "silence-long", "scene-figee", "volume", "video-duree-differente", "video-absente", "timeline-absente",
    "sous-titre-mal-decoupe", "voix-infidele", "voix-plate", "accroche-imparfaite",
})


def error_code(message: str) -> str:
    for code, pattern in COMPILED:
        if pattern.search(message):
            return code
    return DEFAULT_ERROR


def count(codes: list[str]) -> dict:
    out: dict = {}
    for code in codes:
        out[code] = out.get(code, 0) + 1
    return out
