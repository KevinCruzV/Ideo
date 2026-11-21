import contextlib
import os
import sys
import traceback
from pathlib import Path

from ideo import common, cost, pipeline, plan_check

USAGE = ("usage : python -m ideo prepare <url> | cost <job> | check <job> | produce <job> [--part N] "
         "| status <job> | deepen <job>")
COMMANDS = ("prepare", "cost", "check", "produce", "status", "deepen")


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


def parse(argv: list[str]) -> tuple[str, str, int | None]:
    if not argv or argv[0] not in COMMANDS:
        raise UsageError(USAGE)
    cmd, rest = argv[0], argv[1:]
    part = None
    if cmd == "produce" and "--part" in rest:
        i = rest.index("--part")
        if i + 1 >= len(rest) or not rest[i + 1].isdigit():
            raise UsageError("--part attend un numéro de partie, par exemple --part 2")
        part = int(rest[i + 1])
        rest = rest[:i] + rest[i + 2:]
    if len(rest) != 1:
        raise UsageError(USAGE)
    return cmd, rest[0], part


def _paths(paths) -> str:
    return " ; ".join(str(p) for p in paths)


def run(cmd: str, arg: str, part: int | None) -> tuple[list[str], int]:
    if cmd == "prepare":
        job, info = pipeline.prepare(arg)
        return [f"OK prepare : {job} ({info['words']} mots, langue {info['lang']}, {info['paragraphs']} paragraphes, "
                f"{info['sfx']} sons). Transcription : {job / 'transcript_compact.md'} ({cost.reading_note(job)}). "
                f"Coût estimé : {cost.line(job)}"], 0
    job = pipeline.resolve_job(arg)
    if cmd == "cost":
        if not pipeline.prepared(job):
            raise common.IdeoError(f"{job.name} n'est pas préparé : lance d'abord prepare <url>.")
        return [f"OK cost : {cost.line(job)}. Transcription : {job / 'transcript_compact.md'} ({cost.reading_note(job)})"], 0
    if cmd == "check":
        errors = plan_check.check_plan(job)
        if errors:
            return [f"ERREUR check : {e}" for e in errors], 1
        plan = common.load_json(job / "plan.json")
        count = len(plan["parts"])
        what = "1 vidéo" if count == 1 else f"{count} parties"
        return [f"OK check : {what}. Relecture : {job / 'plan.md'}"], 0
    if cmd == "produce":
        return [f"OK produce : {_paths(pipeline.produce(job, part))}"], 0
    if cmd == "status":
        return [f"OK status : {pipeline.status(job)}"], 0
    return [f"OK deepen : nouveau job {pipeline.deepen(job)}"], 0


def _log_for(cmd: str, arg: str) -> tuple[Path, Path | None]:
    job = None
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
        cmd, arg, part = parse(argv)
    except UsageError as err:
        print(f"ERREUR ideo : {err}")
        return 1
    log, job = _log_for(cmd, arg)
    try:
        with quiet(log):
            try:
                out, code = run(cmd, arg, part)
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
