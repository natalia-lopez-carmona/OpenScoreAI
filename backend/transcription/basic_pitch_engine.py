"""Motor de transcripción: audio → MIDI usando Basic Pitch (backend ONNX).

Basic Pitch (Spotify) detecta las notas de un audio polifónico y produce
un objeto `pretty_midi.PrettyMIDI`, que guardamos como archivo .mid.
"""
from __future__ import annotations

import logging
from pathlib import Path

# Silenciamos los avisos de backends no instalados (usamos ONNX a propósito).
logging.getLogger().setLevel(logging.ERROR)

from basic_pitch import ICASSP_2022_MODEL_PATH
from basic_pitch.inference import predict


def transcribe_to_midi(
    audio_path: str | Path,
    output_midi_path: str | Path,
    *,
    onset_threshold: float = 0.5,
    frame_threshold: float = 0.3,
    minimum_note_length: float = 127.70,
) -> Path:
    """Transcribe un archivo de audio a MIDI.

    Args:
        audio_path: ruta al audio de entrada (wav, flac, ogg, mp3...).
        output_midi_path: ruta donde se guardará el .mid resultante.
        onset_threshold: sensibilidad al inicio de nota (0-1). Más alto = menos notas.
        frame_threshold: sensibilidad al sostenido de nota (0-1).
        minimum_note_length: duración mínima de nota en milisegundos.

    Returns:
        La ruta del archivo MIDI generado.
    """
    audio_path = Path(audio_path)
    output_midi_path = Path(output_midi_path)

    _model_output, midi_data, _note_events = predict(
        str(audio_path),
        ICASSP_2022_MODEL_PATH,
        onset_threshold=onset_threshold,
        frame_threshold=frame_threshold,
        minimum_note_length=minimum_note_length,
    )

    output_midi_path.parent.mkdir(parents=True, exist_ok=True)
    midi_data.write(str(output_midi_path))
    return output_midi_path
