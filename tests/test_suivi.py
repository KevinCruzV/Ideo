import os
import time

import pytest

from ideo import cli, common, suivi


def progress_lines(job):
    return [line.split(" ", 2)[2] for line in (job / "logs" / "progress.log").read_text(encoding="utf-8").splitlines()]


def test_run_arrete_une_commande_muette(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "STALL_SECONDS", 1)
    start = time.monotonic()
    with pytest.raises(common.IdeoError, match="aucune activité depuis"):
        common.run(["sleep", "30"], tmp_path / "x.log")
    assert time.monotonic() - start < 10
    assert "bloquée" in (tmp_path / "x.log").read_text(encoding="utf-8")


def test_run_laisse_finir_une_commande_qui_ecrit(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "STALL_SECONDS", 1)
    log = tmp_path / "x.log"
    common.run(["sh", "-c", "for i in 1 2 3 4; do echo $i; sleep 0.5; done"], log)
    assert log.read_text(encoding="utf-8").split() == ["1", "2", "3", "4"]


def test_etape_note_le_debut_la_fin_et_la_duree(tmp_path):
    with suivi.etape(tmp_path, "render-01"):
        lines = progress_lines(tmp_path)
        assert lines == ["DÉBUT render-01"]
        assert (tmp_path / "logs" / "en-cours.json").exists()
    lines = progress_lines(tmp_path)
    assert lines[1].startswith("OK render-01 (") and lines[1].endswith(" s)")
    assert not (tmp_path / "logs" / "en-cours.json").exists()


def test_etape_garde_le_detail_de_la_ligne_ok(tmp_path):
    with suivi.etape(tmp_path, "fetch") as step:
        step.detail = "audio et métadonnées"
    assert progress_lines(tmp_path)[1].startswith("OK fetch : audio et métadonnées (")


def test_etape_note_l_echec(tmp_path):
    with pytest.raises(common.IdeoError):
        with suivi.etape(tmp_path, "voice-01"):
            raise common.IdeoError("plus de crédit")
    assert progress_lines(tmp_path)[1].startswith("ERREUR voice-01 : plus de crédit (")
    assert not (tmp_path / "logs" / "en-cours.json").exists()


@pytest.mark.parametrize("text,expected", [
    ("Rendered 0/5605\nRendered 2240/5605, time remaining: 1m\n", "images 2240/5605 (40 %)"),
    ("Rendered 5604/5605\nEncoded 4430/5605\n", "encodage 4430/5605 (79 %)"),
    ("Bundling...\n", None),
])
def test_avancement_du_rendu(text, expected):
    assert suivi.avancement_rendu(text) == expected


def test_rapport_etape_en_cours(tmp_path):
    with suivi.etape(tmp_path, "render-01"):
        (tmp_path / "logs" / "render-01.log").write_text("Rendered 100/1000\n", encoding="utf-8")
        line = suivi.rapport(tmp_path)
    assert line.startswith("en cours : render-01 depuis ")
    assert "images 100/1000 (10 %)" in line
    assert "bloqué" not in line


def test_rapport_signale_un_blocage(tmp_path, monkeypatch):
    with suivi.etape(tmp_path, "render-01"):
        log = tmp_path / "logs" / "render-01.log"
        log.write_text("Rendered 100/1000\n", encoding="utf-8")
        old = time.time() - 20 * 60
        os.utime(log, (old, old))
        os.utime(tmp_path / "logs" / "progress.log", (old, old))
        line = suivi.rapport(tmp_path)
    assert "probablement bloqué" in line and "render-01.log" in line


def test_rapport_signale_un_processus_disparu(tmp_path):
    common.progress(tmp_path, "DÉBUT voice-01")
    common.save_json(tmp_path / "logs" / "en-cours.json", {"step": "voice-01", "pid": 999999, "start": time.time()})
    assert "arrêté sans message" in suivi.rapport(tmp_path)


def test_rapport_termine(tmp_path):
    with suivi.etape(tmp_path, "sources"):
        pass
    assert suivi.rapport(tmp_path).startswith("terminé")


def test_rapport_sans_rien(tmp_path):
    assert suivi.rapport(tmp_path) == "rien n'a encore été lancé"


def test_commande_suivi(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("IDEO_HOME", str(tmp_path))
    job = tmp_path / "jobs" / "abcdefghijk"
    job.mkdir(parents=True)
    with suivi.etape(job, "assemble-01"):
        pass
    assert cli.main(["suivi", str(job)]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and out[0].startswith("OK suivi : terminé")


def test_run_voit_la_sortie_d_un_script_python_au_fil_de_l_eau(tmp_path, monkeypatch):
    import sys

    monkeypatch.setattr(common, "STALL_SECONDS", 1.5)
    log = tmp_path / "x.log"
    script = "import time\nfor i in range(4):\n    print(i)\n    time.sleep(0.8)\n"
    common.run([sys.executable, "-c", script], log)
    assert log.read_text(encoding="utf-8").split() == ["0", "1", "2", "3"]


def test_run_arrete_la_commande_si_python_est_interrompu(tmp_path, monkeypatch):
    import subprocess

    made = []
    real = subprocess.Popen

    def spy(*args, **kwargs):
        proc = real(*args, **kwargs)
        made.append(proc)
        return proc

    monkeypatch.setattr(common.subprocess, "Popen", spy)
    calls = {"n": 0}
    real_monotonic = common.time.monotonic

    def interrupt():
        calls["n"] += 1
        if calls["n"] > 2:
            raise KeyboardInterrupt
        return real_monotonic()

    monkeypatch.setattr(common.time, "monotonic", interrupt)
    with pytest.raises(KeyboardInterrupt):
        common.run(["sleep", "30"], tmp_path / "x.log")
    monkeypatch.setattr(common.time, "monotonic", real_monotonic)
    assert made and made[0].poll() is not None
