import pytest

from ideo import cli, common, cost


def make_job(tmp_path, words=2808, lang="fr", duration=1080, transcript_chars=16830, skip=None):
    job = tmp_path / "job"
    job.mkdir(parents=True)
    common.save_json(job / "words.json", [{"w": "mot", "s": i * 0.38, "e": i * 0.38 + 0.3} for i in range(words)])
    common.save_json(job / "info.json", {"duration": duration, "channel": "C", "title": "T"})
    (job / "lang.txt").write_text(lang, encoding="utf-8")
    (job / "transcript_compact.md").write_text("x" * transcript_chars, encoding="utf-8")
    if skip is not None:
        common.save_json(job / "skip.json", skip)
    for step in ("fetch", "transcribe", "transcript"):
        common.mark(job, step, True)
    return job


@pytest.mark.parametrize("chars,lang,tokens", [(3300, "fr", 1000), (4000, "en", 1000), (3500, "de", 1000)])
def test_tokens_use_one_ratio_per_language(chars, lang, tokens):
    assert cost.tokens(chars, lang) == tokens


def test_reading_is_transcript_plus_skill_and_guide(tmp_path):
    est = cost.estimate(make_job(tmp_path))
    skill = sum(len(p.read_text(encoding="utf-8")) for p in cost.SKILL_FILES)
    assert est["transcript"] == cost.round_hundred(16830 / 3.3) == 5100
    assert est["skill"] == cost.round_hundred(skill / 3.3)
    assert est["reading"] == est["transcript"] + est["skill"]


def test_writing_range_follows_expected_output_duration(tmp_path):
    est = cost.estimate(make_job(tmp_path))
    seconds = 2808 / 2.6 * cost.OUTPUT_SHARE
    assert est["seconds"] == pytest.approx(seconds)
    assert est["videos"] == 1
    assert est["write_low"] == cost.round_hundred(seconds * cost.WRITE_TOKENS_PER_SECOND)
    assert est["write_high"] == cost.round_hundred(seconds * cost.WRITE_TOKENS_PER_SECOND * cost.WRITE_SPREAD)


def test_sponsor_speech_does_not_count(tmp_path):
    full = cost.estimate(make_job(tmp_path))
    half = cost.estimate(make_job(tmp_path / "b", skip={"hidden": [{"s": 0, "e": 533.5, "probable": True}],
                                                        "segments": []}))
    assert half["seconds"] == pytest.approx(full["seconds"] / 2, rel=0.01)


def test_short_source_is_raised_to_the_minimum(tmp_path):
    est = cost.estimate(make_job(tmp_path, words=50, duration=30))
    assert est["seconds"] == 45 and est["videos"] == 1


def test_long_source_expects_several_videos(tmp_path):
    est = cost.estimate(make_job(tmp_path, words=20000, duration=8000))
    assert est["videos"] == 4 and est["seconds"] == pytest.approx(20000 / 2.6 * cost.OUTPUT_SHARE)


def test_line_marks_every_figure_as_an_estimate(tmp_path):
    line = cost.line(make_job(tmp_path))
    skill = cost.estimate(make_job(tmp_path / "b"))["skill"]
    assert line.startswith(f"lecture ~{cost.fmt(5100 + skill)} tokens (transcription 5 100 + skill et guide {cost.fmt(skill)}), ")
    assert "écriture ~2 800 à 4 400 tokens, source 18 min, 1 vidéo attendue" in line
    assert chr(0x2014) not in line


def test_missing_files_never_raise(tmp_path):
    job = tmp_path / "empty"
    job.mkdir()
    assert "lecture ~" in cost.line(job)


def test_cli_cost_prints_one_ok_line(tmp_path, capsys):
    job = make_job(tmp_path)
    assert cli.main(["cost", str(job)]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out == [f"OK cost : {cost.line(job)}"]


def test_cli_cost_needs_a_prepared_job(tmp_path, capsys):
    job = tmp_path / "job"
    job.mkdir()
    assert cli.main(["cost", str(job)]) == 1
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and out[0].startswith("ERREUR cost : ") and "prepare" in out[0]
