import contextlib
import os
import sys
import traceback
from pathlib import Path

from ideo import codes, common, cost, countries, eleven, entretien, history, learn, lexicon, music, photo, pipeline, plan_check, qc, retours, review, rythme, setup_voix

USAGE = ("usage : python -m ideo prepare <url> | cost <job> | check <job> [--sans-relecture] | produce <job> [--part N] [--payer] "
         "| qc <job> | status <job> | deepen <job> | learn \"<leçon>\" | learn --bug \"<constat>\" [job] | learn --prononciation \"mot=graphie\" [--lang fr] "
         "| photo <job> \"<nom de la personne>\" | photo-manuel <job> \"<nom>\" <fichier> \"<source>\" | musique <job> <choix> | musique <job> --dernier | musique --liste | musique-lien \"<type>\" | voix-liste | voix-test [\"phrase\"] | setup-voix | finale <job> | entretien [--fait \"<résumé>\" | --echec \"<raison>\"] "
         "| rythme <job ou fichier vidéo> [--seuil 0.3]")
COMMANDS = ("prepare", "cost", "check", "produce", "qc", "status", "deepen", "learn", "entretien", "photo", "photo-manuel", "setup-voix", "musique", "voix-liste", "voix-test", "musique-lien", "finale", "rythme")


class UsageError(Exception):
    pass


@contextlib.contextmanager
def quiet(log: Path):
    log.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout.flush()
    sys.stderr.flush()
    saved = (sys.stdout, sys.stderr)
    fds = (os.dup(1), os.dup(2))
    with log.open("a", encoding="utf-8") as f:
        os.dup2(f.fileno(), 1)
        os.dup2(f.fileno(), 2)
        sys.stdout = sys.stderr = f
        try:
            yield
        finally:
            f.flush()
            sys.stdout, sys.stderr = saved
            os.dup2(fds[0], 1)
            os.dup2(fds[1], 2)
            os.close(fds[0])
            os.close(fds[1])


def parse(argv: list[str]) -> tuple[str, str, int | None, dict]:
    if not argv or argv[0] not in COMMANDS:
        raise UsageError(USAGE)
    cmd, rest = argv[0], argv[1:]
    part = None
    opts: dict = {}
    if cmd == "learn":
        if rest[:1] == ["--bug"]:
            if not 2 <= len(rest) <= 3:
                raise UsageError(USAGE)
            opts = {"bug": True, "job": rest[2] if len(rest) == 3 else None}
            return cmd, rest[1], None, opts
        if rest[:1] == ["--prononciation"]:
            lang = "fr"
            tail = rest[1:]
            if "--lang" in tail:
                i = tail.index("--lang")
                if i + 1 >= len(tail) or len(tail) != i + 2 or i != 1:
                    raise UsageError(USAGE)
                lang = tail[i + 1]
                tail = tail[:i]
            if len(tail) != 1:
                raise UsageError(USAGE)
            return cmd, tail[0], None, {"prononciation": True, "lang": lang}
        if len(rest) != 1:
            raise UsageError(USAGE)
        return cmd, rest[0], None, opts
    if cmd == "setup-voix":
        if rest:
            raise UsageError(USAGE)
        return cmd, "", None, opts
    if cmd == "voix-liste":
        if rest:
            raise UsageError(USAGE)
        return cmd, "", None, opts
    if cmd == "voix-test":
        return cmd, " ".join(rest), None, opts
    if cmd == "musique-lien":
        return cmd, " ".join(rest), None, opts
    if cmd == "musique":
        if rest == ["--liste"]:
            return cmd, "", None, {"liste": True}
        if len(rest) == 2 and rest[1] == "--dernier" and not rest[0].startswith("--"):
            return cmd, rest[0], None, {"dernier": True}
        if len(rest) < 2 or rest[0].startswith("--"):
            raise UsageError(USAGE)
        return cmd, rest[0], None, {"choix": " ".join(rest[1:])}
    if cmd == "photo":
        if len(rest) < 2 or rest[0].startswith("--"):
            raise UsageError(USAGE)
        return cmd, rest[0], None, {"name": " ".join(rest[1:])}
    if cmd == "photo-manuel":
        if len(rest) != 4:
            raise UsageError(USAGE)
        return cmd, rest[0], None, {"name": rest[1], "file": rest[2], "source": rest[3]}
    if cmd == "entretien":
        if not rest:
            return cmd, "", None, opts
        if rest[0] == "--fait" and len(rest) <= 2:
            return cmd, rest[1] if len(rest) == 2 else "", None, {"fait": True}
        if rest[0] == "--echec" and len(rest) == 2:
            return cmd, rest[1], None, {"echec": True}
        raise UsageError(USAGE)
    if cmd == "produce" and "--part" in rest:
        i = rest.index("--part")
        if i + 1 >= len(rest) or not rest[i + 1].isdigit():
            raise UsageError("--part attend un numéro de partie, par exemple --part 2")
        part = int(rest[i + 1])
        rest = rest[:i] + rest[i + 2:]
    if cmd == "produce" and "--payer" in rest:
        rest = [r for r in rest if r != "--payer"]
        opts["payer"] = True
    if cmd == "check" and "--sans-relecture" in rest:
        rest = [r for r in rest if r != "--sans-relecture"]
        opts["sans_relecture"] = True
    if cmd == "rythme" and "--seuil" in rest:
        i = rest.index("--seuil")
        try:
            seuil = float(rest[i + 1]) if i + 1 < len(rest) else None
        except ValueError:
            seuil = None
        if seuil is None:
            raise UsageError("--seuil attend un nombre, par exemple --seuil 0.3")
        opts["seuil"] = seuil
        rest = rest[:i] + rest[i + 2:]
    if len(rest) != 1:
        raise UsageError(USAGE)
    return cmd, rest[0], part, opts


def _paths(paths) -> str:
    return " ; ".join(str(p) for p in paths)


def run(cmd: str, arg: str, part: int | None, opts: dict | None = None) -> tuple[list[str], int]:
    opts = opts or {}
    if cmd == "learn":
        return _learn(arg, opts), 0
    if cmd == "entretien":
        return _entretien(arg, opts), 0
    if cmd == "setup-voix":
        return [f"OK setup-voix : {setup_voix.run()}"], 0
    if cmd == "musique-lien":
        return [f"OK musique-lien : {music.search_link(arg)}"], 0
    if cmd == "voix-liste":
        voices = eleven.list_voices()
        return [f"OK voix-liste : {len(voices)} voix{'' if len(voices) < 2 else ''}"] + [
            f"{v['name']} | {v['id']} | {v['detail']}" if v["detail"] else f"{v['name']} | {v['id']}" for v in voices], 0
    if cmd == "voix-test":
        phrase = arg.strip() or eleven.DEFAULT_TEST
        target = common._root() / "voix-test.wav"
        characters, seconds = eleven.try_phrase(phrase, target)
        return [f"OK voix-test : {characters} caractères consommés, durée {seconds:.1f} s, fichier {target}"], 0
    if cmd == "musique" and opts.get("liste"):
        lines = music.listing()
        return [f"OK musique : {len(lines)} morceau{'x' if len(lines) > 1 else ''}"] + lines, 0
    if cmd == "prepare":
        job, info = pipeline.prepare(arg)
        return [f"OK prepare : {job} ({info['words']} mots, langue {info['lang']}, {info['paragraphs']} paragraphes, "
                f"{info['sfx']} sons). Transcription : {job / 'transcript_compact.md'} ({cost.reading_note(job)}). "
                f"Coût estimé : {cost.line(job)}.{cost.advice(job)}{setup_voix.install_note(info['lang'])}{_notice_tail()}"], 0
    if cmd == "rythme":
        return _rythme(arg, opts), 0
    job = pipeline.resolve_job(arg)
    if cmd == "photo":
        return [photo.run(job, opts["name"])], 0
    if cmd == "photo-manuel":
        return [photo.add_manual(job, opts["name"], Path(opts["file"]), opts["source"])], 0
    if cmd == "finale":
        return [_finale(job)], 0
    if cmd == "musique" and opts.get("dernier"):
        name, seconds = music.take_latest(job)
        stamp = f"{int(seconds) // 60}:{int(seconds) % 60:02d}" if seconds else "durée inconnue"
        return [f"OK musique : {name} ({stamp})"], 0
    if cmd == "musique":
        return [f"OK musique : {music.choose_for(job, opts['choix'])}"], 0
    if cmd == "cost":
        if not pipeline.prepared(job):
            raise common.IdeoError(f"{job.name} n'est pas préparé : lance d'abord prepare <url>.")
        return [f"OK cost : {cost.line(job)}.{cost.advice(job)} Transcription : {job / 'transcript_compact.md'} "
                f"({cost.reading_note(job)})"], 0
    if cmd == "check":
        result = plan_check.analyze(job)
        errors = result["errors"]
        if errors:
            _safely(history.add_errors, job, codes.count([codes.error_code(e) for e in errors]))
            return [f"ERREUR check : {e}" for e in errors], 1
        stats = result["stats"]
        plan = stats["plan"]
        _safely(history.note_plan, job, stats["lang"], stats["source"], stats["scenes"])
        flag_pairs = []
        for wish in _safely(history.new_wishes, job, plan.get("wishes") or []) or []:
            hit = countries.flag_wish(wish)
            if hit:
                flag_pairs.append(("drapeau-existe", f"RELIRE : Plan : le drapeau de {hit[1]} existe : écris « flag:{hit[0]} »"))
            else:
                _safely(retours.add_wish, wish)
        count = len(plan["parts"])
        what = "1 vidéo" if count == 1 else f"{count} parties"
        pairs = [] if opts.get("sans_relecture") else review.relire_coded(job, plan, stats["seconds"])
        pairs = flag_pairs + pairs
        if pairs:
            _safely(history.add_relire, job, [c for c, _ in pairs])
        lines = [text for _, text in pairs]
        points = ""
        if lines:
            points = f", {len(lines)} point{'s' if len(lines) > 1 else ''} à relire"
        head = f"OK check : {what}, {stats['scenes']} scènes, environ {stats['seconds']} s{points}{_eleven_chars(plan)}. Relecture : {job / 'plan.md'}"
        return [head] + lines, 0
    if cmd == "produce":
        outputs = pipeline.produce(job, part, pay=bool(opts.get("payer")))
        review.reset(job)
        return [f"OK produce : {_paths(outputs)} ; {' ; '.join(_after_produce(job, part))}"], 0
    if cmd == "qc":
        alerts = qc.run(job)
        return [f"OK qc : {qc.summary(job, alerts)}"] + [f"ALERTE : {a}" for a in alerts], 0
    if cmd == "status":
        return [f"OK status : {pipeline.status(job)}"], 0
    return [f"OK deepen : nouveau job {pipeline.deepen(job)}"], 0


def _rythme(arg: str, opts: dict) -> list[str]:
    path = Path(arg).expanduser()
    seuil = opts.get("seuil", rythme.SEUIL_SCENE)
    if path.is_file():
        mesure = rythme.depuis_video(path, seuil=seuil)
        return [f"OK rythme : {rythme.rapport(mesure, label=path.name)}"]
    job = pipeline.resolve_job(arg)
    mesures = rythme.depuis_job(job)
    return [f"OK rythme : {job.name}"] + [rythme.rapport(m, label=f"partie {n}") for n, m in sorted(mesures.items())]


ENGINE_NAMES = {"elevenlabs": "ElevenLabs", "kyutai": "locale Kyutai", "edge": "en ligne"}


def _finale(job: Path) -> str:
    from ideo import config, voice

    final = config.final_engine()
    if final == config.draft_engine():
        raise common.IdeoError("aucune voix finale différente du brouillon : ajoute une clé ElevenLabs "
                               "(python -m ideo.cle) ou choisis « engine » dans config.json.")
    if not (job / "plan.json").exists():
        raise common.IdeoError("plan.json est introuvable : écris d'abord le plan.")
    plan = common.load_json(job / "plan.json")
    config.mark_final(job)
    cost = ""
    if final == "elevenlabs":
        total = sum(len(text) for part in plan["parts"] for _, text in voice.segments(plan, part))
        cost = f", environ {total} caractères ElevenLabs"
    return f"OK finale : voix {ENGINE_NAMES.get(final, final)}{cost}. Lance produce pour refaire la voix et le rendu."


def _eleven_chars(plan: dict) -> str:
    from ideo import config, voice

    if config.engine() != "elevenlabs":
        return ""
    total = 0
    for part in plan["parts"]:
        total += sum(len(text) for _, text in voice.segments(plan, part))
    return f", environ {total} caractères ElevenLabs pour la version finale"


def _notice_tail() -> str:
    note = _safely(history.take_notice)
    return f" {note}" if note else ""


def _safely(fn, *args):
    try:
        return fn(*args)
    except Exception:
        return None


def _produced_seconds(job: Path) -> float | None:
    total, found = 0.0, False
    for path in sorted((job / "parts").glob("*/timeline.json")):
        try:
            tl = common.load_json(path)
            total += tl["durationInFrames"] / tl["fps"]
            found = True
        except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError):
            continue
    return total if found else None


def _learn_from_run(job: Path, pairs: list) -> list[str]:
    history.add_qc(job, [c for c, _ in pairs])
    history.record_produce(job, _produced_seconds(job))
    for code, message in pairs:
        if code in codes.CODE_ONLY:
            _safely(retours.add_detected, code, job.name, message)
    return [f"Leçon automatique : {lesson}" for lesson in (_safely(learn.auto_lessons) or [])]


def _draft_note(job: Path) -> list[str]:
    from ideo import config

    if config.is_final(job) or config.final_engine() == config.draft_engine():
        return []
    return [f"Voix : brouillon gratuit, lance finale pour la voix {ENGINE_NAMES.get(config.final_engine(), config.final_engine())}"]


def _voice_notes(job: Path, part: int | None) -> list[str]:
    notes = []
    characters = None
    for path in sorted((job / "parts").glob("*/voice-info.json")):
        if part is not None and path.parent.name != f"{part:02d}":
            continue
        info = common.load_json(path)
        if info.get("fallback"):
            where = "locale" if info.get("engine") == "kyutai" else "en ligne"
            note = f"Voix : repli sur la voix {where}, {info['fallback']}"
        elif info.get("engine") == "elevenlabs":
            characters = (characters or 0) + int(info.get("characters") or 0)
            continue
        elif info.get("local_missing"):
            note = "Voix : voix en ligne, la voix locale n'est pas installée"
        else:
            continue
        if note not in notes:
            notes.append(note)
    if characters is not None:
        notes.insert(0, f"Voix : ElevenLabs, {characters} caractères")
    for path in sorted((job / "parts").glob("*/music.json")):
        if part is not None and path.parent.name != f"{part:02d}":
            continue
        info = common.load_json(path)
        if info.get("missing") and "Musique : aucun morceau trouvé" not in notes:
            notes.append("Musique : aucun morceau trouvé")
    return notes


def _after_produce(job: Path, part: int | None) -> list[str]:
    voice_notes = (_safely(_voice_notes, job, part) or []) + (_safely(_draft_note, job) or [])
    try:
        pairs = qc.run_coded(job, part)
        pieces = [qc.summary(job, [text for _, text in pairs])]
    except Exception as err:
        return [f"Contrôle : indisponible ({type(err).__name__} : {err})"] + voice_notes
    pieces += voice_notes
    pieces += _safely(_learn_from_run, job, pairs) or []
    note = _safely(entretien.notice)
    if note:
        pieces.append(note.rstrip("."))
    return pieces


def _entretien(arg: str, opts: dict) -> list[str]:
    if opts.get("fait"):
        history.entretien_done(arg)
        return ["OK entretien : fait, enregistré" + (f" ({arg})" if arg else "")]
    if opts.get("echec"):
        history.entretien_failed(arg)
        return [f"OK entretien : échec enregistré ({arg})"]
    return [entretien.report_line()]


def _learn(arg: str, opts: dict) -> list[str]:
    if opts.get("prononciation"):
        word, sep, spoken = arg.partition("=")
        if not sep:
            raise common.IdeoError("une prononciation s'écrit « mot=graphie », par exemple « face=fasse ».")
        lexicon.add(word, spoken, opts["lang"])
        return [f"OK learn : prononciation enregistrée ({word.strip()} se dira « {spoken.strip()} »)"]
    if opts.get("bug"):
        job = None
        if opts.get("job"):
            try:
                job = pipeline.resolve_job(opts["job"]).name
            except common.IdeoError:
                job = Path(opts["job"]).name
        return [f"OK learn : retour enregistré dans {learn.add_bug(arg, job)}"]
    number, path = learn.add_lesson(arg)
    return [f"OK learn : leçon {number}/{learn.MAX_LESSONS} enregistrée dans {path}"]


def _log_for(cmd: str, arg: str) -> tuple[Path, Path | None]:
    job = None
    if cmd in ("learn", "entretien", "setup-voix", "voix-liste", "voix-test") or cmd == "musique-lien" or (cmd == "musique" and arg == ""):
        return common.JOBS / "cli.log", None
    try:
        job = common.job_dir(arg) if cmd == "prepare" else pipeline.resolve_job(arg)
    except common.IdeoError:
        pass
    if job is None:
        return common.JOBS / "cli.log", None
    return job / "logs" / "cli.log", job


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    try:
        cmd, arg, part, opts = parse(argv)
    except UsageError as err:
        print(f"ERREUR ideo : {err}")
        return 1
    log, job = _log_for(cmd, arg)
    try:
        with quiet(log):
            try:
                out, code = run(cmd, arg, part, opts)
            except common.IdeoError as err:
                out, code = [f"ERREUR {cmd} : {err}"], 1
            except Exception as err:
                traceback.print_exc()
                out, code = [f"ERREUR {cmd} : erreur inattendue ({type(err).__name__} : {err}). Détails : {log}"], 1
    except OSError as err:
        out, code = [f"ERREUR {cmd} : journal inutilisable {log} ({err})"], 1
    if job is not None and cmd in ("prepare", "produce") and code:
        pipeline.progress(job, out[0])
    print("\n".join(out))
    return code
