"""Exportación de MusicXML a PDF usando el CLI de MuseScore 4.

Llamamos directamente al ejecutable de MuseScore (más robusto que la ruta
interna de music21). El grabado musical (engraving) lo hace MuseScore.

Requiere MuseScore instalado. Se puede forzar la ruta con la variable de
entorno MUSESCORE_PATH.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

# Ubicaciones habituales del ejecutable en Windows.
_WINDOWS_CANDIDATES = (
    r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
    r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe",
)


def find_musescore() -> str | None:
    """Localiza el ejecutable de MuseScore. Devuelve la ruta o None."""
    # 1) Variable de entorno explícita.
    env = os.environ.get("MUSESCORE_PATH")
    if env and Path(env).exists():
        return env
    # 2) En el PATH del sistema.
    for name in ("MuseScore4", "mscore", "musescore", "MuseScore3"):
        found = shutil.which(name)
        if found:
            return found
    # 3) Rutas típicas de instalación en Windows.
    for cand in _WINDOWS_CANDIDATES:
        if Path(cand).exists():
            return cand
    return None


def musicxml_to_pdf(musicxml_path: str | Path, output_pdf_path: str | Path) -> Path:
    """Convierte un MusicXML en PDF mediante MuseScore.

    Raises:
        RuntimeError: si MuseScore no está instalado o la conversión falla.
    """
    musicxml_path = Path(musicxml_path)
    output_pdf_path = Path(output_pdf_path)

    musescore = find_musescore()
    if not musescore:
        raise RuntimeError(
            "MuseScore no encontrado. Instálalo (winget install Musescore.Musescore) "
            "o define la variable de entorno MUSESCORE_PATH."
        )

    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [musescore, str(musicxml_path), "-o", str(output_pdf_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0 or not output_pdf_path.exists():
        raise RuntimeError(f"MuseScore falló (código {result.returncode}): {result.stderr.strip()}")

    return output_pdf_path
