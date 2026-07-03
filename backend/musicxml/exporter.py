"""Exportación de MIDI a MusicXML usando music21.

MusicXML es el formato estándar de partitura editable (lo abren MuseScore,
Finale, Sibelius, etc.). No requiere software externo, a diferencia del PDF.
"""
from __future__ import annotations

from pathlib import Path

from music21 import converter


# Rejilla de cuantización: divisores del pulso (negra).
#   4 → hasta semicorcheas (1/16)   ·   3 → tresillos
_QUANTIZE_DIVISORS = (4, 3)


def midi_to_musicxml(
    midi_path: str | Path,
    output_path: str | Path,
    *,
    quantize: bool = True,
) -> Path:
    """Convierte un archivo MIDI en MusicXML con notación legible.

    Pasos de limpieza (Basic Pitch da tiempos "crudos"):
      1. Cuantización de inicios y duraciones a una rejilla (semicorcheas + tresillos).
      2. makeNotation: divide en compases y añade silencios, plicas y barrado.

    Args:
        midi_path: ruta al .mid de entrada.
        output_path: ruta donde se guardará el .musicxml.
        quantize: si False, exporta sin cuantizar (tiempos crudos).

    Returns:
        La ruta del archivo MusicXML generado.
    """
    midi_path = Path(midi_path)
    output_path = Path(output_path)

    score = converter.parse(str(midi_path))

    if quantize:
        # 1) Alinear inicios y duraciones a la rejilla musical.
        try:
            score.quantize(
                _QUANTIZE_DIVISORS,
                processOffsets=True,
                processDurations=True,
                inPlace=True,
            )
        except Exception:
            pass  # ante un caso raro, seguimos y exportamos igual.

    # 2) Notación real: compases, silencios, plicas y barrado.
    #    Sin esto la partitura no tiene silencios ni figuras bien agrupadas.
    try:
        score.makeNotation(inPlace=True)
    except Exception:
        pass

    output_path.parent.mkdir(parents=True, exist_ok=True)
    score.write("musicxml", fp=str(output_path))
    return output_path
