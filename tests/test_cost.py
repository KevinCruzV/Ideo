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
    assert est["long"] is False
    assert est["write_low"] == cost.round_hundred(seconds * cost.WRITE_TOKENS_PER_SECOND)
    assert est["write_high"] == cost.round_hundred(seconds * cost.WRITE_TOKENS_PER_SECOND * cost.WRITE_SPREAD)


def test_sponsor_speech_does_not_count(tmp_path):
    full = cost.estimate(make_job(tmp_path))
    half = cost.estimate(make_job(tmp_path / "b", skip={"hidden": [{"s": 0, "e": 533.5, "probable": True}],
                                                        "segments": []}))
    assert half["seconds"] == pytest.approx(full["seconds"] / 2, rel=0.01)


def test_short_source_is_raised_to_the_minimum(tmp_path):
    est = cost.estimate(make_job(tmp_path, words=50, duration=30))
    assert est["seconds"] == 65 and est["long"] is False


def words_for(seconds):
    return round(seconds / cost.OUTPUT_SHARE * 2.6)


def test_content_just_over_one_video_is_not_called_long(tmp_path):
    est = cost.estimate(make_job(tmp_path, words=words_for(400), duration=4000))
    assert est["long"] is False and est["seconds"] == 300
    line = cost.line(make_job(tmp_path / "b", words=words_for(400), duration=4000))
    assert "vidéos" not in line and "contenu long" not in line and "attendue" not in line


def test_content_far_over_one_video_is_called_long(tmp_path):
    margin = 300 * cost.LONG_CONTENT_FACTOR
    assert cost.estimate(make_job(tmp_path, words=words_for(margin - 10), duration=8000))["long"] is False
    est = cost.estimate(make_job(tmp_path / "b", words=words_for(margin + 10), duration=8000))
    assert est["long"] is True and est["seconds"] == 300
    line = cost.line(make_job(tmp_path / "c", words=words_for(margin + 10), duration=8000))
    assert line.endswith("contenu long : une vidéo de 5 min ou plusieurs parties")
    assert "vidéos attendues" not in line


def test_line_marks_every_figure_as_an_estimate(tmp_path):
    line = cost.line(make_job(tmp_path))
    skill = cost.estimate(make_job(tmp_path / "b"))["skill"]
    assert line.startswith(f"lecture au moins ~{cost.fmt(5100 + skill)} tokens (transcription 5 100 + skill et guide {cost.fmt(skill)}), ")
    assert line.endswith("écriture ~2 800 à 4 400 tokens, source 18 min")
    assert chr(0x2014) not in line


def test_missing_files_never_raise(tmp_path):
    job = tmp_path / "empty"
    job.mkdir()
    assert "lecture au moins ~" in cost.line(job)


def test_cli_cost_prints_one_ok_line(tmp_path, capsys):
    job = make_job(tmp_path)
    assert cli.main(["cost", str(job)]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out == [f"OK cost : {cost.line(job)}.{cost.advice(job)} Transcription : {job.resolve() / 'transcript_compact.md'} "
                   f"({cost.reading_note(job)})"]


def test_cli_cost_needs_a_prepared_job(tmp_path, capsys):
    job = tmp_path / "job"
    job.mkdir()
    assert cli.main(["cost", str(job)]) == 1
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and out[0].startswith("ERREUR cost : ") and "prepare" in out[0]


def reading_job(tmp_path, text, lang="fr"):
    job = tmp_path / "r"
    job.mkdir(parents=True)
    (job / "lang.txt").write_text(lang, encoding="utf-8")
    (job / "transcript_compact.md").write_text(text, encoding="utf-8")
    return job


def test_short_transcript_is_one_read(tmp_path):
    job = reading_job(tmp_path, "Titre : T\n\n[0:00] bonjour\n[0:05] au revoir\n")
    assert cost.reading(job) == {"lines": 4, "chunk": None, "offsets": []}
    assert cost.reading_note(job) == "4 lignes, à lire en un seul Read"


def test_long_transcript_gets_fixed_chunks_covering_every_line_once(tmp_path):
    line = "[0:00] " + "mot " * 100
    job = reading_job(tmp_path, "\n".join([line] * 300) + "\n")
    plan = cost.reading(job)
    chunk = plan["chunk"]
    assert chunk == int(cost.READ_TOKENS * 3.3) // len(line.strip())
    assert plan["offsets"] == list(range(1, 301, chunk))
    note = cost.reading_note(job)
    offsets = ", ".join(str(o) for o in plan["offsets"])
    assert note == (f"300 lignes, trop longue pour un seul Read : lis-la en {len(plan['offsets'])} Read consécutifs, "
                    f"offset {offsets}, chacun avec limit {chunk}")


def test_two_hour_source_is_read_in_chunks(tmp_path):
    from ideo import compact

    words = [{"w": "parole" if i % 7 else "longuement", "s": i * 0.44, "e": i * 0.44 + 0.3} for i in range(18000)]
    text, _ = compact.build(words, [], {"title": "T", "channel": "C", "duration": 7980})
    job = reading_job(tmp_path, text)
    plan = cost.reading(job)
    assert plan["lines"] == len(text.splitlines()) and plan["lines"] > 250
    longest = max(len(line) for line in text.splitlines())
    assert plan["chunk"] * longest <= cost.READ_TOKENS * 3.3
    assert plan["offsets"][-1] <= plan["lines"] < plan["offsets"][-1] + plan["chunk"]


def test_source_under_a_minute_is_shown_in_seconds(tmp_path):
    assert cost.line(make_job(tmp_path, words=50, duration=25)).endswith("source 25 s")
    assert cost.line(make_job(tmp_path / "b", words=50, duration=90)).endswith("source 2 min")


def test_cost_line_carries_the_advised_duration(tmp_path, capsys):
    job = make_job(tmp_path)
    assert cost.advice(job).startswith(" Durée conseillée : ")
    assert "jusqu'à 300 s si elle en a besoin" in cost.advice(job)
    assert "Durée conseillée" in capsys.readouterr().out if cli.main(["cost", str(job)]) == 0 else False


def test_lessons_file_counts_in_the_reading_estimate():
    names = [p.name for p in cost.SKILL_FILES]
    assert "lecons.md" in names and all(p.exists() for p in cost.SKILL_FILES)
