import contextlib
import os
import sys
import traceback
from pathlib import Path

from ideo import common, cost, learn, pipeline, plan_check, qc, review

USAGE = ("usage : python -m ideo prepare <url> | cost <job> | check <job> [--sans-relecture] | produce <job> [--part N] "
         "| qc <job> | status <job> | deepen <job> | learn \"<leçon>\" | learn --bug \"<constat>\" [job]")
COMMANDS = ("prepare", "cost", "check", "produce", "qc", "status", "deepen", "learn")


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
        if len(rest) != 1:
            raise UsageError(USAGE)
        return cmd, rest[0], None, opts
    if cmd == "produce" and "--part" in rest:
        i = rest.index("--part")
        if i + 1 >= len(rest) or not rest[i + 1].isdigit():
            raise UsageError("--part attend un numéro de partie, par exemple --part 2")
        part = int(rest[i + 1])
        rest = rest[:i] + rest[i + 2:]
    if cmd == "check" and "--sans-relecture" in rest:
        rest = [r for r in rest if r != "--sans-relecture"]
        opts["sans_relecture"] = True
    if len(rest) != 1:
        raise UsageError(USAGE)
    return cmd, rest[0], part, opts


def _paths(paths) -> str:
    return " ; ".join(str(p) for p in paths)


def run(cmd: str, arg: str, part: int | None, opts: dict | None = None) -> tuple[list[str], int]:
    opts = opts or {}
    if cmd == "learn":
        return _learn(arg, opts), 0
    if cmd == "prepare":
        job, info = pipeline.prepare(arg)
        return [f"OK prepare : {job} ({info['words']} mots, langue {info['lang']}, {info['paragraphs']} paragraphes, "
                f"{info['sfx']} sons). Transcription : {job / 'transcript_compact.md'} ({cost.reading_note(job)}). "
                f"Coût estimé : {cost.line(job)}.{cost.advice(job)}"], 0
    job = pipeline.resolve_job(arg)
    if cmd == "cost":
        if not pipeline.prepared(job):
            raise common.IdeoError(f"{job.name} n'est pas préparé : lance d'abord prepare <url>.")
        return [f"OK cost : {cost.line(job)}.{cost.advice(job)} Transcription : {job / 'transcript_compact.md'} "
                f"({cost.reading_note(job)})"], 0
    if cmd == "check":
        errors = plan_check.check_plan(job)
        if errors:
            return [f"ERREUR check : {e}" for e in errors], 1
        stats = plan_check.analyze(job)["stats"]
        plan = stats["plan"]
        count = len(plan["parts"])
        what = "1 vidéo" if count == 1 else f"{count} parties"
        lines = [] if opts.get("sans_relecture") else review.relire(job, plan, stats["seconds"])
        points = ""
        if lines:
            points = f", {len(lines)} point{'s' if len(lines) > 1 else ''} à relire"
        head = f"OK check : {what}, {stats['scenes']} scènes, environ {stats['seconds']} s{points}. Relecture : {job / 'plan.md'}"
        return [head] + lines, 0
    if cmd == "produce":
        outputs = pipeline.produce(job, part)
        review.reset(job)
        return [f"OK produce : {_paths(outputs)} ; {_control(job, part)}"], 0
    if cmd == "qc":
        alerts = qc.run(job)
        return [f"OK qc : {qc.summary(job, alerts)}"] + [f"ALERTE : {a}" for a in alerts], 0
    if cmd == "status":
        return [f"OK status : {pipeline.status(job)}"], 0
    return [f"OK deepen : nouveau job {pipeline.deepen(job)}"], 0


def _control(job: Path, part: int | None) -> str:
    try:
        return qc.summary(job, qc.run(job, part))
    except Exception as err:
        return f"Contrôle : indisponible ({type(err).__name__} : {err})"


def _learn(arg: str, opts: dict) -> list[str]:
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
    if cmd == "learn":
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
