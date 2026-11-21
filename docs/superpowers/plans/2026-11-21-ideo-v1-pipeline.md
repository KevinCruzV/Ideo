# ideo v1 : pipeline complet, plan de construction

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** à partir d'une URL YouTube, produire de 1 à 8 shorts MP4 verticaux dans la direction artistique
retenue (géométrie en papier découpé, fond ivoire), avec une voix de synthèse de repli, en ne faisant travailler
Claude qu'une fois (écriture de `plan.json`).

**Architecture :** plugin Claude Code lancé depuis le clone local. Un paquet Python `ideo` (CLI
`python -m ideo <étape> <job>`) fait fetch, transcription, validation du plan, voix, assemblage audio et calcul de
la timeline. Un projet Remotion (`render/`, pnpm) rend chaque partie à partir d'un `timeline.json`. Le skill
`ideo` orchestre et c'est le seul endroit où Claude lit et écrit.

**Tech Stack :** Python 3.11+, yt-dlp, faster-whisper, edge-tts, numpy, pytest ; Node 20+, pnpm, Remotion 4,
React, TypeScript ; ffmpeg.

**Spec :** `docs/superpowers/specs/2026-11-21-ideo-design.md`

**Hors de ce plan (plans suivants) :** le clone de voix (Chatterbox / F5-TTS, skill `setup-voix`), la conception
de la mascotte et de la bibliothèque de pictogrammes. Ici la mascotte est un emplacement en pointillés marqué
`[MASCOTTE]` (règle anti-slop R-23) et les pictogrammes se limitent aux formes géométriques de base.

## Global Constraints

- macOS sur Apple Silicon uniquement (spec §12). Le skill `setup` refuse un Mac Intel avec un message clair.
- Node : pnpm uniquement, jamais npm ni yarn.
- Sortie : MP4 H.264 + AAC, 1080x1920, 30 im/s, loudness normalisée à -14 LUFS (`loudnorm=I=-14:TP=-1.5:LRA=11`).
- Durée (spec §9, mise à jour) : une seule vidéo par défaut, de 45 à 300 s ; découpage en parties (8 au maximum, 45 à 300 s chacune)
  seulement si le contenu utile dépasse 300 s. Avec une seule vidéo : pas de "Partie 1" à l'écran, fin "prochaine vidéo".
- Ordre d'une partie : accroche (2 à 3 s) -> scènes -> fin "abonne-toi" (2 à 3 s) (spec §13, §14).
- La langue du short est celle de la vidéo source, détectée à la transcription (spec §8). Citations jamais traduites.
- Watermark : texte "Ideo", étiquette papier en haut à droite, présente du début à la fin (spec §13).
- Couleurs : fond `#f4efe4`, rouge `#e2462c`, jaune `#f5bf2a`, bleu `#2747c9`, papier crème `#fbf6ea`, encre
  `#1f1a14`. Une seule couleur d'accent par écran (spec §5.4 bis).
- Typo : Bricolage Grotesque (textes, sous-titres), Unbounded (watermark). Polices embarquées dans `render/`,
  pas de chargement réseau au rendu.
- Animation "stop-motion" : positions et rotations quantifiées à 12 im/s (pas de 2,5 images) dans une vidéo à 30 im/s.
- Sous-titres karaoké : groupes de 2 à 4 mots, mot prononcé sur une bande de papier de couleur, mots suivants à 40 % d'opacité.
- Aucun caractère tiret cadratin (U+2014) dans les textes affichés (anti-slop R-02) : le validateur le refuse.
- Aucun chiffre ou fait inventé dans les accroches (anti-slop R-17, R-36) : consigne du guide d'écriture.
- Crédits : Claude ne lit que `transcript_compact.md` et n'écrit que `plan.json`. Les scripts n'affichent qu'une
  ligne de résultat par étape, le reste va dans `jobs/<id>/logs/`.
- `jobs/`, `voice/`, `.venv/`, `render/node_modules/`, `render/out/` sont dans `.gitignore`.

## Review Focus

1. Vidéo sans parole exploitable ou très courte (moins de 2 min, ou musique seule) : `transcribe` doit le dire
   clairement et le skill proposer une seule partie ou l'abandon, sans planter. Test dans la tâche 3.
2. URL privée, supprimée, en direct ou soumise à restriction d'âge : `fetch` sort avec un message lisible et ne
   laisse pas de job à moitié écrit marqué comme réussi. Test dans la tâche 2.
3. Mot d'ancrage introuvable dans la retranscription de la voix (nombres écrits en chiffres et dits en lettres,
   élisions, accents, ponctuation) : correspondance normalisée, puis repli sur une position proportionnelle dans
   la scène, jamais d'arrêt. Test dans la tâche 6.
4. Citation qui ne figure pas mot pour mot dans la transcription : le validateur la refuse en citant le passage
   le plus proche, pour que Claude corrige sans relire toute la transcription. Test dans la tâche 4.
5. Langue autre que français ou anglais (espagnol, allemand…) : une voix de repli est choisie pour la langue
   détectée, les textes fixes (fin, "Partie") ont une traduction ou retombent sur l'anglais. Tests dans les tâches 5 et 6.

---

## Structure des fichiers

```
ideo/
  .claude-plugin/plugin.json
  .gitignore
  README.md
  requirements.txt
  pytest.ini
  ideo/                      paquet Python (racine du repo sur sys.path)
    __init__.py
    __main__.py              CLI : sous-commandes
    common.py                chemins de job, statut, exécution de commandes, JSON
    fetch.py                 métadonnées + audio source
    transcribe.py            faster-whisper -> words.json, lang
    compact.py               words.json -> transcript_compact.md (+ repères de sons)
    sfx.py                   détection des passages sonores sans parole
    plan_check.py            validation de plan.json
    textmatch.py             normalisation et recherche de suites de mots
    i18n.py                  textes fixes par langue
    voice.py                 interface synthesize + backend edge-tts + retranscription
    assemble.py              assemblage audio d'une partie (voix + extraits source)
    timeline.py              ancres -> images, sous-titres, timeline.json
    render.py                appel Remotion, sources.md, description.txt
  tests/
    conftest.py
    fixtures/                petits fichiers de test (words, plan, wav générés)
    test_*.py
  render/                    projet Remotion (pnpm)
    package.json  tsconfig.json  remotion.config.ts
    public/fonts/            BricolageGrotesque-*.ttf, Unbounded-ExtraBold.ttf
    src/index.ts  src/Root.tsx  src/Short.tsx
    src/types.ts             types de timeline.json (miroir de timeline.py)
    src/theme.ts             couleurs, polices, tailles
    src/paper/               PaperShape, PaperStrip, useStopMotion, jitter
    src/chrome/              Watermark, ChapterLabel, Progress, Captions
    src/scenes/              un fichier par type de scène + registry.ts
    fixtures/all-scenes.json timeline de test qui utilise chaque type
  skills/
    ideo/SKILL.md
    ideo/references/plan-guide.md
    setup/SKILL.md
  docs/superpowers/specs/  docs/superpowers/plans/  docs/mockups/
```

## Contrats de données (référencés par les tâches)

**`jobs/<id>/`** : `info.json`, `source.wav` (16 kHz mono), `words.json`, `lang.txt`, `transcript_compact.md`,
`sfx.json`, `plan.json`, `plan.md`, `parts/NN/` (`seg_*.wav`, `seg_*.words.json`, `part.wav`, `offsets.json`,
`timeline.json`), `out/partie-NN.mp4`, `out/sources.md`, `out/description.txt`, `status.json`, `logs/`.

**`words.json`** : `[{"w": str, "s": float, "e": float}]`, secondes.

**`plan.json`** (écrit par Claude, version 1) :

```json
{
  "version": 1,
  "lang": "fr",
  "series_title": "Pourquoi on oublie",
  "parts": [
    {
      "n": 1,
      "title": "L'oubli",
      "hook": "Dis-moi pourquoi tu oublies ce que tu viens de lire ?",
      "scenes": [
        {
          "type": "shape-diagram",
          "say": "Le lundi tout est clair, le jeudi il ne reste presque rien.",
          "props": {"shape": "circle", "values": [1, 0.6, 0.35, 0.15], "labels": ["lundi", "jeudi"]},
          "items": [{"el": "values.0", "on": "lundi"}, {"el": "values.3", "on": "jeudi"}],
          "src": "12:30"
        },
        {
          "type": "quote",
          "say": "Lui-même le résume ainsi.",
          "props": {"text": "we forget most of it within a day", "speaker": "Hermann Ebbinghaus"},
          "src": "14:05"
        }
      ]
    }
  ]
}
```

- `say` : texte de la voix off de la scène. `items[].on` doit apparaître dans `say`.
- `src` : `mm:ss` ou `h:mm:ss` du paragraphe de la transcription compacte qui justifie la scène.
- Scène `quote` : `props.text` est une suite de mots présente dans la transcription près de `src` ; l'extrait
  audio correspondant est joué après `say`.
- Scène avec `"sfx": "12:31"` : joue le son source repéré à ce repère (liste dans `sfx.json`).
- Types de scène v1 (noms anglais des composants de la spec §5.4) : `key-title` (titre-cle), `person-card`
  (carte-personne), `fact-chips` (etiquettes-faits), `stack-list` (liste-empilee), `counter` (compteur),
  `timeline` (frise), `icon-grid` (grille-pictos), `stamp` (tampon), `quote` (citation), `object-state`
  (decor-objet), `shape-diagram` (schéma en formes), `mascot` (mascotte). Les composants `hook`, `outro`, chrome et
  sous-titres sont ajoutés par la timeline, pas par Claude.

**`timeline.json`** (produit par `timeline.py`, lu par Remotion) :

```json
{
  "fps": 30, "width": 1080, "height": 1920, "durationInFrames": 2310,
  "lang": "fr", "audio": "part.wav", "watermark": "Ideo",
  "chapter": {"part": 1, "total": 5, "title": "L'oubli", "label": "Partie"},
  "segments": [
    {"kind": "hook", "from": 0, "to": 84, "props": {"text": "..."}, "items": []},
    {"kind": "scene", "type": "shape-diagram", "from": 84, "to": 400,
     "props": {}, "items": [{"el": "values.0", "at": 96}]},
    {"kind": "outro", "from": 2230, "to": 2310, "props": {"text": "Abonne-toi pour la partie 2 : ..."}}
  ],
  "captions": [{"words": [{"w": "Dis-moi", "from": 0, "to": 9}], "from": 0, "to": 30}]
}
```

---

### Task 1 : Socle du repo et utilitaires de job

**Files:**
- Create: `.claude-plugin/plugin.json`, `.gitignore`, `README.md`, `requirements.txt`, `pytest.ini`,
  `ideo/__init__.py`, `ideo/common.py`, `tests/conftest.py`, `tests/test_common.py`

**Interfaces:**
- Produces:
  - `ROOT: Path` (env `IDEO_HOME`, défaut : racine du repo), `JOBS: Path = ROOT / "jobs"`
  - `job_dir(url: str) -> Path` : `jobs/<id-vidéo-youtube>`, créé si absent
  - `read_status(job: Path) -> dict` / `mark(job: Path, step: str, ok: bool, detail: str = "") -> None`
    (écrit `status.json` : `{"steps": {step: {"ok": bool, "detail": str, "at": iso}}}`)
  - `run(cmd: list[str], log: Path) -> None` : stdout/stderr dans `log`, lève `IdeoError(message lisible)` si code ≠ 0
  - `class IdeoError(Exception)`
  - `save_json(path, obj)`, `load_json(path)`
  - `parse_ts(s: str) -> float` (`"12:30"` -> 750.0, `"1:02:03"` -> 3723.0) et `fmt_ts(sec: float) -> str`

- [ ] **Step 1 : tests**

```python
def test_job_dir_uses_youtube_id(tmp_path, monkeypatch):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    d = common.job_dir("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10")
    assert d == tmp_path / "jobs" / "dQw4w9WgXcQ" and d.is_dir()
    assert common.job_dir("https://youtu.be/dQw4w9WgXcQ") == d

def test_mark_and_read_status(tmp_path):
    common.mark(tmp_path, "fetch", True, "ok")
    assert common.read_status(tmp_path)["steps"]["fetch"]["ok"] is True

def test_run_raises_readable_error(tmp_path):
    with pytest.raises(common.IdeoError):
        common.run(["false"], tmp_path / "x.log")

def test_timestamps():
    assert common.parse_ts("12:30") == 750.0
    assert common.parse_ts("1:02:03") == 3723.0
    assert common.fmt_ts(3723.4) == "1:02:03"
    assert common.fmt_ts(75) == "1:15"
```

- [ ] **Step 2 :** `python -m pytest tests/test_common.py -q` -> échec (module absent)
- [ ] **Step 3 :** implémenter `ideo/common.py` ; `plugin.json` (`name: "ideo"`, `skills: ["./skills/"]`) ;
  `.gitignore` selon les Global Constraints ; `requirements.txt` (yt-dlp, faster-whisper, edge-tts, numpy, pytest) ;
  `pytest.ini` avec le marqueur `network` (tests qui touchent Internet, exclus par défaut : `-m "not network"`).
- [ ] **Step 4 :** `python -m pytest -q` -> PASS
- [ ] **Step 5 :** commit `chore: socle du repo et utilitaires de job`

### Task 2 : fetch

**Files:**
- Create: `ideo/fetch.py`, `tests/test_fetch.py`

**Interfaces:**
- Consumes: `job_dir`, `run`, `mark`, `IdeoError`, `save_json`
- Produces: `fetch(url: str) -> Path` : écrit `info.json` (`id, title, channel, webpage_url, duration,
  chapters, language`) et `source.wav` (16 kHz mono) ; ne télécharge que l'audio ; idempotent (ne refait rien si
  `source.wav` existe et `status.fetch.ok`).
- `explain_ytdlp_error(stderr: str) -> str` : traduit en message lisible.

- [ ] **Step 1 : tests**

```python
@pytest.mark.parametrize("stderr,expected", [
    ("ERROR: [youtube] x: Private video", "vidéo privée"),
    ("ERROR: [youtube] x: Video unavailable", "indisponible"),
    ("ERROR: Sign in to confirm your age", "restriction d'âge"),
    ("ERROR: [youtube] x: This live event will begin", "en direct"),
])
def test_explain_ytdlp_error(stderr, expected):
    assert expected in fetch.explain_ytdlp_error(stderr)

def test_failed_fetch_marks_status_not_ok(tmp_path, monkeypatch):
    # run() simulé qui lève IdeoError("ERROR: Private video")
    ...
    with pytest.raises(common.IdeoError):
        fetch.fetch("https://youtu.be/abcdefghijk")
    assert common.read_status(job)["steps"]["fetch"]["ok"] is False
    assert not (job / "source.wav").exists()

@pytest.mark.network
def test_fetch_real_short_video(): ...   # vidéo publique de moins de 1 min, vérifie info.json et source.wav
```

- [ ] **Step 2 :** pytest -> FAIL
- [ ] **Step 3 :** implémenter avec `python -m yt_dlp -J` puis `-f bestaudio -x` vers un fichier temporaire, puis
  `ffmpeg -ac 1 -ar 16000` vers `source.wav` ; écriture dans un fichier temporaire puis renommage (pas de fichier à moitié écrit).
- [ ] **Step 4 :** pytest -> PASS
- [ ] **Step 5 :** commit `feat: fetch de l'audio et des métadonnées YouTube`

### Task 3 : transcription, repères de sons, transcription compacte

**Files:**
- Create: `ideo/transcribe.py`, `ideo/sfx.py`, `ideo/compact.py`, `tests/test_compact.py`, `tests/test_sfx.py`,
  `tests/test_transcribe.py`

**Interfaces:**
- Produces:
  - `transcribe(job: Path, model: str = "small") -> list[dict]` : `words.json` + `lang.txt` (code ISO détecté par
    faster-whisper). Lève `IdeoError("pas assez de parole : …")` si moins de 150 mots.
    Modèle `small` en int8 sur CPU (Apple Silicon).
  - `find_sfx(rms_db: np.ndarray, words: list[dict], min_len: float = 0.8) -> list[dict]` : passages d'au moins
    `min_len` s sans mot et dont le volume dépasse la médiane de 6 dB -> `[{"at": "12:31", "s": 751.2, "e": 753.6}]`
  - `compact(words: list[dict], sfx: list[dict], info: dict) -> str` : en-tête (titre, chaîne, durée, langue,
    chapitres YouTube s'il y en a), puis paragraphes `[mm:ss] texte` coupés sur une pause ≥ 1,2 s ou à 60 mots,
    et repères `[son mm:ss 2.4s]` insérés à leur place. Aucun minutage par mot.

- [ ] **Step 1 : tests**

```python
def test_compact_paragraphs_on_pause_and_length():
    words = [{"w": "a", "s": i * 0.3, "e": i * 0.3 + 0.2} for i in range(130)]
    text = compact.compact(words, [], {"title": "T", "channel": "C", "duration": 60})
    paras = [l for l in text.splitlines() if l.startswith("[")]
    assert len(paras) == 3 and paras[0].startswith("[0:00]")

def test_compact_inserts_sfx_marker():
    ...
    assert "[son 0:10 2.0s]" in text

def test_find_sfx_detects_loud_gap():
    # 30 s, parole jusqu'à 10 s puis de 13 s à 30 s, pic de volume entre 10.5 et 12.5
    assert sfx.find_sfx(rms, words)[0]["at"] == "0:10"

def test_find_sfx_ignores_quiet_gap(): ...

def test_too_little_speech_raises(tmp_path, monkeypatch):
    # transcription simulée de 40 mots
    with pytest.raises(common.IdeoError, match="pas assez de parole"):
        transcribe.transcribe(job)
```

- [ ] **Step 2 :** pytest -> FAIL
- [ ] **Step 3 :** implémenter ; la transcription utilise faster-whisper (`word_timestamps=True, vad_filter=True`) ; le volume par seconde pour `find_sfx` vient de `source.wav`.
- [ ] **Step 4 :** pytest -> PASS
- [ ] **Step 5 :** commit `feat: transcription, repères de sons et transcription compacte`

### Task 4 : validation du plan

**Files:**
- Create: `ideo/textmatch.py`, `ideo/plan_check.py`, `tests/test_textmatch.py`, `tests/test_plan_check.py`,
  `tests/fixtures/plan_ok.json`, `tests/fixtures/words_small.json`

**Interfaces:**
- Produces:
  - `normalize(word: str) -> str` : minuscules, sans accents ni ponctuation, apostrophes unifiées
  - `find_span(words: list[str], needle: str, start: int = 0) -> tuple[int, int] | None` : indices du premier et
    du dernier mot de `needle` dans `words` (comparaison normalisée)
  - `closest_passage(words: list[dict], needle: str) -> str` : `"[mm:ss] …"` du passage qui partage le plus de mots
  - `check_plan(job: Path) -> list[str]` : liste d'erreurs lisibles, vide si OK ; écrit aussi `plan.md`
    (version lisible : par partie, accroche, puis `say` de chaque scène avec son type, et la liste des extraits
    audio source retenus avec leur minutage, spec §10) si le plan est valide.
  - `SCENE_TYPES: frozenset[str]` (les 12 types du contrat)
  - `estimate_seconds(text: str, lang: str) -> float` : 2,6 mots/s en `fr`, 2,8 en `en`, 2,6 sinon

Règles vérifiées : `version == 1` ; `lang` égal à `lang.txt` ; 1 ≤ parties ≤ 8 ; numéros 1..n ; `hook` non vide ;
type connu ; chaque `items[].on` présent dans `say` ; `src` valide et dans la durée ; citation trouvée dans les
mots à ± 90 s de `src` ; `sfx` présent dans `sfx.json` ; aucun U+2014 dans les textes ; durée estimée d'une partie
(accroche + say + citations + 3 s de fin) entre 55 et 95 s, sinon erreur qui donne la durée estimée.

- [ ] **Step 1 : tests**

```python
def test_find_span_is_accent_and_case_insensitive():
    assert textmatch.find_span(["Il", "a", "été", "créé"], "ete CREE") == (2, 3)

def test_valid_plan_has_no_errors(job_with_fixtures):
    assert plan_check.check_plan(job_with_fixtures) == []
    assert (job_with_fixtures / "plan.md").exists()

@pytest.mark.parametrize("mutate,fragment", [
    (lambda p: p["parts"][0]["scenes"][0]["items"].append({"el": "x", "on": "absent"}), "« absent » n'est pas dans le texte"),
    (lambda p: p["parts"].extend([dict(p["parts"][0], n=i) for i in range(2, 10)]), "8 parties au maximum"),
    (lambda p: p["parts"][0].update(hook="Pourquoi — vraiment ?"), "tiret cadratin"),
    (lambda p: p["parts"][0]["scenes"][0].update(type="carousel"), "type inconnu"),
    (lambda p: p.update(lang="de"), "langue"),
])
def test_plan_errors(job_with_fixtures, mutate, fragment): ...

def test_quote_not_found_points_to_closest_passage(job_with_fixtures):
    # citation légèrement fausse : l'erreur contient le [mm:ss] du passage le plus proche
    ...

def test_part_too_short_reports_estimate(job_with_fixtures): ...
```

- [ ] **Step 2 :** pytest -> FAIL
- [ ] **Step 3 :** implémenter
- [ ] **Step 4 :** pytest -> PASS
- [ ] **Step 5 :** commit `feat: validation de plan.json`

### Task 5 : voix (interface + repli edge-tts) et textes fixes

**Files:**
- Create: `ideo/voice.py`, `ideo/i18n.py`, `tests/test_voice.py`, `tests/test_i18n.py`

**Interfaces:**
- Produces:
  - `class VoiceBackend(Protocol): def synthesize(self, text: str, lang: str, out_wav: Path) -> None`
  - `class EdgeTTSBackend` : voix par langue (`fr` -> `fr-FR-HenriNeural`, `en` -> `en-US-GuyNeural`, `es` ->
    `es-ES-AlvaroNeural`, `de` -> `de-DE-ConradNeural`, `it` -> `it-IT-DiegoNeural`, `pt` -> `pt-BR-AntonioNeural`) ;
    autre langue : `IdeoError("pas de voix pour <lang>")`. Sortie convertie en wav 48 kHz mono.
  - `get_backend() -> VoiceBackend` : seul point qu'un futur backend de clone remplacera (plan suivant).
  - `voice_part(job: Path, n: int, backend: VoiceBackend | None = None) -> list[Path]` : un wav par segment
    (`seg_00_hook.wav`, `seg_01.wav`…, `seg_99_outro.wav`) + `.words.json` par retranscription faster-whisper du
    wav généré (mêmes réglages que la tâche 3, langue forcée). Idempotent par segment.
  - `i18n.t(key: str, lang: str, **kw) -> str` : clés `part_label` ("Partie" / "Part"), `outro_next`
    ("Abonne-toi pour la partie {n} : {title}" / "Follow for part {n}: {title}"), `outro_last`
    ("Abonne-toi pour la prochaine série" / "Follow for the next series"). `fr` et `en` obligatoires ;
    autres langues : traductions pour `es, de, it, pt`, sinon repli sur `en`.

- [ ] **Step 1 : tests**

```python
def test_outro_text_fr_and_fallback():
    assert i18n.t("outro_next", "fr", n=2, title="Le sommeil") == "Abonne-toi pour la partie 2 : Le sommeil"
    assert i18n.t("outro_last", "ja") == i18n.t("outro_last", "en")

def test_voice_part_creates_one_wav_per_segment(job_with_plan, fake_backend, fake_whisper):
    paths = voice.voice_part(job_with_plan, 1, backend=fake_backend)
    assert [p.name for p in paths][0] == "seg_00_hook.wav" and paths[-1].name == "seg_99_outro.wav"
    assert all(p.with_suffix(".words.json").exists() for p in paths)

def test_voice_part_skips_existing_segments(...): ...   # le backend n'est appelé qu'une fois par segment

def test_edge_backend_rejects_unknown_language():
    with pytest.raises(common.IdeoError, match="pas de voix"):
        voice.EdgeTTSBackend().synthesize("x", "xx", Path("/tmp/x.wav"))
```

- [ ] **Step 2 :** pytest -> FAIL
- [ ] **Step 3 :** implémenter ; le texte de fin vient de `i18n` (titre de la partie suivante, ou `outro_last` pour la dernière).
- [ ] **Step 4 :** pytest -> PASS
- [ ] **Step 5 :** commit `feat: voix de repli edge-tts et textes fixes par langue`

### Task 6 : assemblage audio et timeline

**Files:**
- Create: `ideo/assemble.py`, `ideo/timeline.py`, `tests/test_assemble.py`, `tests/test_timeline.py`

**Interfaces:**
- Consumes: `textmatch.find_span`, `textmatch.normalize`, `i18n.t`, sorties de la tâche 5
- Produces:
  - `assemble_part(job: Path, n: int) -> Path` : concatène dans l'ordre accroche, puis pour chaque scène
    `seg_NN.wav` suivi de l'extrait de citation ou du son source s'il y en a (fondu 80 ms à l'entrée et à la sortie,
    0,25 s de silence avant et après), puis la fin ; normalise à -14 LUFS ; écrit `part.wav` et `offsets.json`
    (`[{"seg": "seg_01", "start": float, "end": float, "clip": {"start": float, "end": float} | null}]`).
    Bornes d'une citation = premier et dernier mot trouvés par `find_span` dans `words.json`, marge 0,15 s.
  - `anchor_frame(seg_words: list[dict], anchor: str, seg_start: float, seg_dur: float, say: str, fps: int = 30) -> int` :
    image du premier mot de l'ancre dans la retranscription du segment ; si absent, position proportionnelle de
    l'ancre dans `say` appliquée à la durée du segment.
  - `caption_groups(words: list[dict], fps: int = 30) -> list[dict]` : groupes de 2 à 4 mots, coupure sur
    ponctuation finale ou pause > 0,5 s.
  - `build_timeline(job: Path, n: int, total: int) -> Path` : écrit `timeline.json` (contrat ci-dessus) ; pendant
    un extrait de citation, les sous-titres affichent les mots de la source.

- [ ] **Step 1 : tests**

```python
def test_anchor_found_with_normalisation():
    words = [{"w": "Il", "s": 0.0, "e": 0.2}, {"w": "verrouille,", "s": 0.3, "e": 0.8}]
    assert timeline.anchor_frame(words, "verrouille", seg_start=10.0, seg_dur=1.0, say="Il verrouille") == 309

def test_anchor_missing_falls_back_to_proportional_position():
    # "1885" dit "mille huit cent quatre-vingt-cinq" : absent de la retranscription
    f = timeline.anchor_frame(words, "1885", seg_start=0.0, seg_dur=4.0, say="En 1885 il commence")
    assert 15 <= f <= 45

def test_caption_groups_2_to_4_words_and_break_on_pause(): ...

def test_assemble_inserts_quote_clip_and_writes_offsets(job_with_voice_fixtures):
    # wav sinus générés par ffmpeg dans la fixture ; vérifie l'ordre et les durées dans offsets.json à 0,05 s près
    ...

def test_timeline_has_hook_first_outro_last_and_watermark(job_with_offsets):
    tl = load_json(timeline.build_timeline(job, 1, 3))
    assert tl["segments"][0]["kind"] == "hook" and tl["segments"][-1]["kind"] == "outro"
    assert tl["watermark"] == "Ideo" and tl["width"] == 1080 and tl["height"] == 1920
    assert tl["chapter"] == {"part": 1, "total": 3, "title": "L'oubli", "label": "Partie"}
```

- [ ] **Step 2 :** pytest -> FAIL
- [ ] **Step 3 :** implémenter (ffmpeg pour découpe, `afade`, `concat`, `loudnorm`)
- [ ] **Step 4 :** pytest -> PASS
- [ ] **Step 5 :** commit `feat: assemblage audio et timeline par partie`

### Task 7 : projet Remotion, matière papier et habillage

**Files:**
- Create: `render/package.json`, `render/tsconfig.json`, `render/remotion.config.ts`, `render/src/index.ts`,
  `render/src/Root.tsx`, `render/src/Short.tsx`, `render/src/types.ts`, `render/src/theme.ts`,
  `render/src/paper/PaperShape.tsx`, `render/src/paper/PaperStrip.tsx`, `render/src/paper/stopMotion.ts`,
  `render/src/chrome/Watermark.tsx`, `render/src/chrome/ChapterLabel.tsx`, `render/src/chrome/Progress.tsx`,
  `render/src/chrome/Captions.tsx`, `render/public/fonts/*`, `render/fixtures/minimal.json`
- Test: `render/src/paper/stopMotion.test.ts` (vitest)

**Interfaces:**
- Consumes: contrat `timeline.json`
- Produces:
  - Composition `Short` (id `"Short"`), `calculateMetadata` lit `durationInFrames`, `fps`, `width`, `height` dans les props.
  - `stepFrame(frame: number, fps = 30, stepFps = 12): number` : image quantifiée pour l'effet stop-motion.
  - `jitter(seed: string, frame: number, maxDeg = 2.5): number` : rotation pseudo-aléatoire stable par pas.
  - `<PaperShape kind="circle"|"square"|"strip"|"arrow" color size rotate enterAt>` : forme avec ombre
    `2px 3px 0 rgba(0,0,0,.22)`, entrée en 3 pas stop-motion à `enterAt`.
  - `<PaperStrip text color enterAt>` : bande de texte papier découpée (`clip-path` polygonal, légère rotation).
  - Les quatre éléments d'habillage, toujours rendus par `Short` : watermark en haut à droite, étiquette de
    chapitre en haut à gauche (`"{label} {part} · {title}"`), progression (segments = parties) en bas, sous-titres
    karaoké dans le tiers bas (zone libre de 220 px au-dessus du bord pour l'interface TikTok).

- [ ] **Step 1 : test**

```ts
test("stepFrame quantise à 12 im/s", () => {
  expect([0, 1, 2, 3, 4, 5].map((f) => stepFrame(f))).toEqual([0, 0, 0, 2.5, 2.5, 5]);
});
test("jitter est stable pour un même pas", () => {
  expect(jitter("a", 3)).toBe(jitter("a", 4));
});
```

- [ ] **Step 2 :** `pnpm --dir render test` -> FAIL
- [ ] **Step 3 :** `pnpm --dir render init` du projet Remotion (template vide), polices téléchargées une fois depuis
  Google Fonts dans `public/fonts/` et chargées par `@font-face` local ; implémenter.
- [ ] **Step 4 :** `pnpm --dir render test` PASS, puis
  `pnpm --dir render exec remotion still Short out/minimal.png --props=fixtures/minimal.json --frame=45`
  -> image 1080x1920 avec watermark, étiquette, progression et sous-titres lisibles (contrôle visuel contre
  `docs/mockups/style-fusion.html`).
- [ ] **Step 5 :** commit `feat: projet Remotion, matière papier et habillage`

### Task 8 : composants de scène

**Files:**
- Create: `render/src/scenes/registry.ts` et un fichier par composant : `Hook.tsx`, `Outro.tsx`, `KeyTitle.tsx`,
  `PersonCard.tsx`, `FactChips.tsx`, `StackList.tsx`, `Counter.tsx`, `Timeline.tsx`, `IconGrid.tsx`, `Stamp.tsx`,
  `Quote.tsx`, `ObjectState.tsx`, `ShapeDiagram.tsx`, `Mascot.tsx` ; `render/fixtures/all-scenes.json`
- Test: `render/src/scenes/registry.test.ts`

**Interfaces:**
- Consumes: `PaperShape`, `PaperStrip`, `stepFrame`, `jitter`, `theme`
- Produces: `SCENES: Record<SceneType, React.FC<SceneProps>>` avec
  `SceneProps = { props: Record<string, unknown>; items: { el: string; at: number }[]; from: number; to: number }`.
  Chaque élément listé dans `items` apparaît à son image `at` ; les autres sont visibles dès `from`.
  Props attendues (le guide d'écriture de la tâche 10 les recopie) :
  - `key-title {text, accent}` : `accent` = mot du texte posé sur la bande de couleur
  - `person-card {name, role}` : avatar = rond de papier avec initiales (pas de photo, R-23)
  - `fact-chips {chips: string[]}` · `stack-list {items: string[]}` · `counter {label, from, to}`
  - `timeline {start, end, marks: {at, label}[]}` · `icon-grid {cells: {shape, label}[]}` (formes de base seulement)
  - `stamp {text}` · `quote {text, speaker}` · `shape-diagram {shape, values: number[], labels: string[]}`
  - `object-state {object: "screen"|"board"|"jar"|"door"|"scale", states: string[]}` : un objet construit en
    formes de papier dont l'état change à chaque élément de `items` (texte affiché, remplissage, fissure, bascule)
  - `mascot {bubble}` : emplacement en pointillés `[MASCOTTE]` + bulle de texte
  - `hook {text}` : même animation pour toutes les accroches (signature) · `outro {text}`
  Couleur d'accent : une par écran, en rotation rouge -> jaune -> bleu d'une scène à l'autre.

- [ ] **Step 1 : test**

```ts
test("chaque type de plan_check a un composant", () => {
  const types = ["key-title","person-card","fact-chips","stack-list","counter","timeline",
                 "icon-grid","stamp","quote","object-state","shape-diagram","mascot"];
  types.forEach((t) => expect(SCENES[t as SceneType]).toBeDefined());
});
```

- [ ] **Step 2 :** test -> FAIL
- [ ] **Step 3 :** implémenter ; `all-scenes.json` contient un segment de chaque type plus accroche et fin.
- [ ] **Step 4 :** test PASS, puis `pnpm --dir render exec tsc --noEmit` sans erreur, puis un `remotion still` au
  milieu de chaque segment de `all-scenes.json` (script `pnpm --dir render stills`) : aucune erreur, aucun texte qui
  déborde de son cadre ni ne passe sous les sous-titres (contrôle visuel des 14 images).
- [ ] **Step 5 :** commit `feat: composants de scène en papier découpé`

### Task 9 : rendu, sources et description

**Files:**
- Create: `ideo/render.py`, `tests/test_render.py`

**Interfaces:**
- Consumes: `timeline.json`, `part.wav`, `info.json`, `plan.json`
- Produces:
  - `render_part(job: Path, n: int) -> Path` : `pnpm --dir render exec remotion render Short <out> --props=<timeline>
    --public-dir=<parts/NN>` -> `out/partie-NN.mp4`
  - `write_sources(job: Path) -> Path` : `out/sources.md`, pour chaque partie et scène, lien
    `https://www.youtube.com/watch?v=<id>&t=<sec>s` vers `src`
  - `write_description(job: Path, n: int) -> str` : `out/description-NN.txt` avec titre de la partie et crédit
    "Source : <titre> (<chaîne>) <url>"

- [ ] **Step 1 : tests**

```python
def test_sources_links_use_seconds(job_with_plan):
    text = render.write_sources(job_with_plan).read_text()
    assert "watch?v=abcdefghijk&t=750s" in text

def test_description_credits_source(job_with_plan):
    assert "Source : " in render.write_description(job_with_plan, 1)

@pytest.mark.slow
def test_render_fixture_part(job_with_timeline_fixture):
    mp4 = render.render_part(job, 1)
    probe = ffprobe(mp4)
    assert (probe.width, probe.height, probe.fps) == (1080, 1920, 30)
    assert abs(probe.duration - 4.0) < 0.1
```

- [ ] **Step 2 :** pytest -> FAIL
- [ ] **Step 3 :** implémenter
- [ ] **Step 4 :** `python -m pytest -q -m "not network"` -> PASS (y compris `slow`)
- [ ] **Step 5 :** commit `feat: rendu Remotion, sources et description`

### Task 10 : CLI, skills et guide d'écriture

**Files:**
- Create: `ideo/__main__.py`, `tests/test_cli.py`, `skills/ideo/SKILL.md`, `skills/ideo/references/plan-guide.md`,
  `skills/setup/SKILL.md`

**Interfaces:**
- Consumes: toutes les fonctions précédentes
- Produces: sous-commandes, chacune affichant **une seule ligne** (`OK <étape> : <résumé>` ou
  `ERREUR <étape> : <message>`) et un code de sortie 0/1 :
  - `prepare <url>` : fetch + transcribe + sfx + compact -> affiche le chemin du job et le nombre de mots
  - `check <job>` : `check_plan` -> erreurs une par ligne, ou `OK check : N parties`
  - `produce <job> [--part N]` : voice + assemble + timeline + render pour chaque partie non faite, puis sources
  - `status <job>` : dernière étape réussie et la suivante
- `SKILL.md` (une page) : 1) `prepare` en arrière-plan ; 2) lire `transcript_compact.md` **une seule fois** et
  `references/plan-guide.md` ; 3) écrire `plan.json` en une fois ; 4) `check`, ne corriger que les erreurs
  signalées ; 5) montrer à Kevin le chemin de `plan.md` (pas son contenu) et attendre son accord ; Kevin peut
  corriger lui-même `hook` et `say` dans `plan.json`, ou demander une correction ciblée, puis on relance `check` ; 6) `produce` en
  arrière-plan ; 7) donner les chemins des MP4, de `sources.md` et des descriptions. "approfondis la partie N" :
  ajouter des parties au plan à partir de la même transcription compacte, sans la relire si elle est encore en contexte.
- `plan-guide.md` : schéma de `plan.json`, props de chaque type (copiées de la tâche 8), règles du validateur,
  règles d'écriture : accroche au même format mais phrase adaptée au sujet, "Dis-moi pourquoi…" par défaut quand
  elle colle, pas la même formule deux parties de suite, accroche vraie et tenue par la partie, aucun chiffre
  inventé, pas de tiret cadratin, phrases courtes à dire à voix haute, une idée par scène, citations courtes
  (moins de 8 s), langue = langue de la vidéo.
- `setup/SKILL.md` : vérifie Apple Silicon (`uname -m` = `arm64`), ffmpeg, Python 3.11+, crée `.venv`, installe
  `requirements.txt`, `pnpm --dir render install`, télécharge le modèle whisper `small` une fois.

- [ ] **Step 1 : tests**

```python
def test_cli_prints_single_line(capsys, fake_pipeline):
    assert cli.main(["status", str(job)]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()) == 1

def test_cli_check_lists_errors_and_exits_1(job_with_bad_plan, capsys):
    assert cli.main(["check", str(job_with_bad_plan)]) == 1
    assert "ERREUR" in capsys.readouterr().out

def test_produce_resumes_after_done_parts(...): ...   # une partie déjà rendue n'est pas refaite
```

- [ ] **Step 2 :** pytest -> FAIL
- [ ] **Step 3 :** implémenter la CLI et écrire les trois fichiers de skill
- [ ] **Step 4 :** pytest -> PASS
- [ ] **Step 5 :** commit `feat: CLI et skills ideo`

### Task 11 : essai de bout en bout sur la vidéo de référence

**Files:**
- Modify: `README.md` (installation, utilisation, où sont les fichiers)
- Create: `docs/superpowers/runs/2026-xx-xx-reference.md` (compte rendu)

- [ ] **Step 1 :** dans une session Claude Code ouverte sur le repo, lancer le skill `ideo` sur la vidéo de
  référence fournie par Kevin.
- [ ] **Step 2 :** vérifier : 1 à 8 MP4 dans `out/`, chacun 1080x1920, 30 im/s, entre 60 et 95 s, accroche puis
  fin "abonne-toi" audibles, watermark visible tout du long, sous-titres calés sur la voix, citations jouées avec
  la vraie voix de la source.
- [ ] **Step 3 :** relever la consommation de l'étape plan (tokens lus et écrits, d'après `/cost` ou l'usage de
  session) et la noter dans le compte rendu avec la durée de la vidéo source.
- [ ] **Step 4 :** passer le rendu au crible anti-slop (porte de livraison, blocs 1 à 4, version vidéo : contraste
  des textes, une couleur d'accent par écran, pas de motif "IA") et noter les écarts.
- [ ] **Step 5 :** commit `docs: essai de bout en bout et README`
