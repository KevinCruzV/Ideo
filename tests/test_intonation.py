import wave

import numpy as np
import pytest

from ideo import intonation

RATE = 48000


def _words(text, start=0.0, step=0.3):
    out = []
    for i, token in enumerate(text.split(" ")):
        out.append({"w": token, "s": round(start + i * step, 3), "e": round(start + i * step + step * 0.9, 3)})
    return out


@pytest.mark.parametrize("text,expected", [
    ("Pourquoi l'État a peur des influenceurs ?", ("ouverte", 0)),
    ("Leclerc ou Aldi, qui vole le plus les Français ?", ("ouverte", 3)),
    ("Alors qui encaisse ?", ("ouverte", 1)),
    ("Alors, qui vole le plus ?", ("ouverte", 1)),
    ("Mais concrètement, cette fameuse règle d'or, elle impose quoi à l'État ?", ("ouverte", 8)),
    ("Alors, à quoi bon l'écrire dans la Constitution ?", ("ouverte", 2)),
    ("Où va l'argent ?", ("ouverte", 0)),
    ("Qu'est-ce que ces règles vont changer ?", ("ouverte", 0)),
    ("Tu sais ce qui se passe ?", ("fermee", None)),
    ("Et chez Aldi ?", ("fermee", None)),
    ("Et toi, tu regardes le prix au kilo avant d'acheter ?", ("fermee", None)),
    ("Pour toi, Macron vise les marchés ou les candidats ?", None),
    ("Et toi, tu relis tes cours ou tu les oublies ?", None),
])
def test_kind_fr(text, expected):
    assert intonation.kind(text.split(" "), "fr") == expected


@pytest.mark.parametrize("text,expected", [
    ("Why does it fall?", ("ouverte", 0)),
    ("Is it true?", ("fermee", None)),
    ("Tea or coffee?", None),
])
def test_kind_en(text, expected):
    assert intonation.kind(text.split(" "), "en") == expected


def test_kind_skips_unsupported_language():
    assert intonation.kind(["Warum", "fällt", "es?"], "de") is None


def test_questions_find_each_question_span():
    words = _words("Le prix monte. Et chez Aldi ? Seuls 3 produits. Alors qui encaisse?")
    assert intonation.questions(words) == [(3, 5), (10, 12)]


def test_questions_accept_question_mark_glued_with_nbsp():
    words = _words("Et toi, tu les oublies ? Abonne-toi.")
    assert intonation.questions(words) == [(0, 4)]


def _voice(contour, seconds):
    n = int(seconds * RATE)
    f0 = np.array([contour(i / RATE) for i in range(n)])
    phase = 2 * np.pi * np.cumsum(f0) / RATE
    signal = sum(np.sin(k * phase) / k for k in range(1, 12))
    signal *= 6000 / np.max(np.abs(signal))
    return signal.astype("<i2")


def _write(path, pcm):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())


def _read(path):
    with wave.open(str(path), "rb") as w:
        return w.getparams(), np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")


def _pitch(path, start, end):
    parselmouth = pytest.importorskip("parselmouth")
    pitch = parselmouth.Sound(str(path)).to_pitch(0.01, 75, 500)
    values = pitch.selected_array["frequency"]
    times = pitch.xs()
    keep = (times >= start) & (times <= end) & (values > 0)
    return float(np.median(values[keep]))


def _semitones(a, b):
    return 12 * np.log2(a / b)


def test_flat_closed_question_gets_a_final_rise(tmp_path):
    pytest.importorskip("parselmouth")
    wav = tmp_path / "seg.wav"
    _write(wav, _voice(lambda t: 150.0, 3.0))
    words = _words("Le prix. Et chez Aldi ?", start=0.2, step=0.45)
    params, before = _read(wav)
    changes = intonation.adjust(wav, words, "fr")
    after_params, after = _read(wav)
    assert len(changes) == 1
    assert after_params == params
    assert len(after) == len(before)
    cut = int((words[2]["s"] - 0.06) * RATE)
    assert np.array_equal(after[:cut], before[:cut])
    last = words[4]
    assert _semitones(_pitch(wav, last["e"] - 0.1, last["e"]), 150.0) > 2.5


def test_flat_open_question_gets_a_peak_and_keeps_its_last_word(tmp_path):
    pytest.importorskip("parselmouth")
    wav = tmp_path / "seg.wav"
    _write(wav, _voice(lambda t: 150.0, 2.0))
    words = _words("Pourquoi tu pars ?", start=0.1, step=0.4)
    changes = intonation.adjust(wav, words, "fr")
    assert len(changes) == 1
    first, last = words[0], words[2]
    assert _semitones(_pitch(wav, first["s"], first["e"]), 150.0) > 2.0
    assert abs(_semitones(_pitch(wav, last["s"] + 0.05, last["e"]), 150.0)) < 0.7


def test_open_question_only_touches_the_question_word(tmp_path):
    pytest.importorskip("parselmouth")
    wav = tmp_path / "seg.wav"
    _write(wav, _voice(lambda t: 150.0 + 40.0 * (t < 0.8), 2.4))
    words = _words("Leclerc ou Aldi, qui vole vraiment ?", start=0.1, step=0.35)
    _, before = _read(wav)
    changes = intonation.adjust(wav, words, "fr")
    _, after = _read(wav)
    assert len(changes) == 1 and "« qui »" in changes[0]
    cut = int((words[3]["s"] - 0.1) * RATE)
    assert np.array_equal(after[:cut], before[:cut])
    resume = int((words[5]["s"] + 0.1) * RATE)
    assert np.array_equal(after[resume:], before[resume:])


def test_lively_question_is_left_alone(tmp_path):
    pytest.importorskip("parselmouth")
    wav = tmp_path / "seg.wav"
    words = _words("Et chez Aldi ?", start=0.1, step=0.4)
    rise_from = words[2]["s"]
    _write(wav, _voice(lambda t: 150.0 * 2 ** (max(0.0, t - rise_from) * 25 / 12), 1.4))
    before = wav.read_bytes()
    assert intonation.adjust(wav, words, "fr") == []
    assert wav.read_bytes() == before


def test_no_question_means_no_change_and_no_praat(tmp_path, monkeypatch):
    wav = tmp_path / "seg.wav"
    _write(wav, _voice(lambda t: 150.0, 1.0))
    before = wav.read_bytes()
    monkeypatch.setitem(__import__("sys").modules, "parselmouth", None)
    assert intonation.adjust(wav, _words("Le prix monte."), "fr") == []
    assert wav.read_bytes() == before
