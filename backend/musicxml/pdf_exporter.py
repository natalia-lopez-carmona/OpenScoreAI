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


class MuseScoreNotFound(RuntimeError):
    """MuseScore no está instalado."""


class MuseScoreFailed(RuntimeError):
    """MuseScore se ejecutó pero no pudo grabar el PDF (p. ej. partitura muy densa)."""


def musicxml_to_pdf(
    musicxml_path: str | Path,
    output_pdf_path: str | Path,
    *,
    attempts: int = 2,
) -> Path:
    """Convierte un MusicXML en PDF mediante MuseScore.

    Reintenta ante fallos intermitentes. Distingue "no instalado" de "falló".

    Raises:
        MuseScoreNotFound: si MuseScore no está instalado.
        MuseScoreFailed: si MuseScore no pudo generar el PDF tras varios intentos.
    """
    musicxml_path = Path(musicxml_path)
    output_pdf_path = Path(output_pdf_path)

    musescore = find_musescore()
    if not musescore:
        raise MuseScoreNotFound(
            "MuseScore no encontrado. Instálalo (winget install Musescore.Musescore) "
            "o define la variable de entorno MUSESCORE_PATH."
        )

    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    last_code = None
    for _ in range(max(1, attempts)):
        result = subprocess.run(
            [musescore, str(musicxml_path), "-o", str(output_pdf_path)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode == 0 and output_pdf_path.exists():
            return output_pdf_path
        last_code = result.returncode
        output_pdf_path.unlink(missing_ok=True)

    raise MuseScoreFailed(
        f"MuseScore no pudo grabar el PDF (código {last_code}). "
        "La partitura puede ser demasiado densa."
    )
