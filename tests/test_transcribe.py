"""Prueba end-to-end del endpoint /transcribe.

Genera una melodía sintética (La4, Si4, Do5, Re5) y verifica que la API
devuelve un MIDI válido con notas detectadas. Requiere Basic Pitch instalado.
"""
import numpy as np
import pretty_midi
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def _synth_melody(path, freqs=(440.0, 493.88, 523.25, 587.33), sr=22050, dur=0.5):
    segments = []
    for f in freqs:
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        tone = 0.5 * np.sin(2 * np.pi * f * t)
        ramp = int(sr * 0.02)
        env = np.ones(len(tone))
        env[:ramp] = np.linspace(0, 1, ramp)
        env[-ramp:] = np.linspace(1, 0, ramp)
        segments.append(tone * env)
    sf.write(path, np.concatenate(segments).astype(np.float32), sr)


def test_transcribe_returns_valid_midi(tmp_path):
    wav = tmp_path / "melody.wav"
    _synth_melody(wav)

    with wav.open("rb") as fh:
        resp = client.post("/transcribe", files={"file": ("melody.wav", fh, "audio/wav")})

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/midi"

    midi = tmp_path / "out.mid"
    midi.write_bytes(resp.content)
    pm = pretty_midi.PrettyMIDI(str(midi))
    notes = [n for inst in pm.instruments for n in inst.notes]
    # Debe detectar varias notas (al menos 3 de las 4 de la melodía).
    assert len(notes) >= 3


def test_transcribe_musicxml(tmp_path):
    wav = tmp_path / "melody.wav"
    _synth_melody(wav)

    with wav.open("rb") as fh:
        resp = client.post(
            "/transcribe",
            params={"format": "musicxml"},
            files={"file": ("melody.wav", fh, "audio/wav")},
        )

    assert resp.status_code == 200, resp.text
    assert "musicxml" in resp.headers["content-type"]

    xml = tmp_path / "out.musicxml"
    xml.write_bytes(resp.content)

    # El MusicXML devuelto debe ser parseable por music21 y contener notas.
    from music21 import converter

    score = converter.parse(str(xml))
    notes = list(score.recurse().notes)
    assert len(notes) >= 3


def test_transcribe_pdf(tmp_path):
    # Se salta si MuseScore no está instalado (p. ej. en CI).
    from backend.musicxml.pdf_exporter import find_musescore

    if find_musescore() is None:
        pytest.skip("MuseScore no instalado; se omite la prueba de PDF")

    wav = tmp_path / "melody.wav"
    _synth_melody(wav)

    with wav.open("rb") as fh:
        resp = client.post(
            "/transcribe",
            params={"format": "pdf"},
            files={"file": ("melody.wav", fh, "audio/wav")},
        )

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    # Un PDF válido empieza por la firma "%PDF".
    assert resp.content[:4] == b"%PDF"


def test_transcribe_rejects_bad_format():
    resp = client.post("/transcribe", files={"file": ("x.txt", b"no soy audio", "text/plain")})
    assert resp.status_code == 400
