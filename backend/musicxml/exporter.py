"""Exportación de MIDI a MusicXML usando music21.

MusicXML es el formato estándar de partitura editable (lo abren MuseScore,
Finale, Sibelius, etc.). No requiere software externo, a diferencia del PDF.
"""
from __future__ import annotations

from pathlib import Path

from music21 import converter


def midi_to_musicxml(midi_path: str | Path, output_path: str | Path) -> Path:
    """Convierte un archivo MIDI en MusicXML.

    Args:
        midi_path: ruta al .mid de entrada.
        output_path: ruta donde se guardará el .musicxml.

    Returns:
        La ruta del archivo MusicXML generado.
    """
    midi_path = Path(midi_path)
    output_path = Path(output_path)

    score = converter.parse(str(midi_path))

    # Cuantización ligera: alinea las notas a una rejilla (semicorcheas y
    # tresillos) para que la partitura sea legible. Basic Pitch da tiempos
    # "crudos"; sin esto, el resultado tiene figuras rítmicas extrañas.
    try:
        score.quantize(inPlace=True)
    except Exception:
        # Si la cuantización falla por algún caso raro, exportamos igualmente.
        pass

    output_path.parent.mkdir(parents=True, exist_ok=True)
    score.write("musicxml", fp=str(output_path))
    return output_path
