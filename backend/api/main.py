"""OpenScoreAI — API REST (FastAPI).

Punto de entrada de la aplicación. Arranca con:
    uvicorn backend.api.main:app --reload
"""
from __future__ import annotations

import shutil
import tempfile
import uuid
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

app = FastAPI(
    title="OpenScoreAI",
    description="Convierte audio musical en partituras editables (MIDI, MusicXML, PDF).",
    version="0.1.0",
)

# Raíz del proyecto (…/OpenScoreAI) para localizar el frontend.
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_INDEX = BASE_DIR / "frontend" / "index.html"

# Formatos de audio aceptados.
ALLOWED_AUDIO = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


class OutputFormat(str, Enum):
    """Formato de salida de la transcripción."""

    midi = "midi"
    musicxml = "musicxml"
    pdf = "pdf"

# Carpeta temporal para audios subidos y MIDIs generados.
WORK_DIR = Path(tempfile.gettempdir()) / "openscoreai"
WORK_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Comprobación de vida del servicio."""
    return {"status": "ok", "service": "OpenScoreAI", "version": "0.1.0"}


@app.get("/", tags=["ui"], include_in_schema=False)
def root() -> FileResponse:
    """Sirve la interfaz web (frontend/index.html)."""
    return FileResponse(FRONTEND_INDEX, media_type="text/html")


@app.post("/transcribe", tags=["transcription"])
def transcribe(
    file: UploadFile = File(...),
    format: OutputFormat = OutputFormat.midi,
    separate_vocals: bool = False,
) -> FileResponse:
    """Recibe un audio y devuelve su transcripción como MIDI, MusicXML o PDF.

    - `format=midi` → archivo .mid (por defecto).
    - `format=musicxml` → archivo .musicxml (partitura editable en MuseScore/Finale).
    - `format=pdf` → partitura en PDF (requiere MuseScore instalado).
    - `separate_vocals=true` → aísla la voz con Demucs antes de transcribir
      (útil para canciones completas; requiere PyTorch/Demucs instalados).

    Nota: se define como función síncrona (`def`) a propósito; FastAPI la ejecuta
    en un hilo aparte, evitando bloquear el bucle de eventos durante la inferencia.
    """
    # Importación diferida: así la API arranca rápido aunque el modelo tarde en cargar.
    from backend.transcription.basic_pitch_engine import transcribe_to_midi

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_AUDIO:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado ({suffix!r}). Usa: {', '.join(sorted(ALLOWED_AUDIO))}",
        )

    uid = uuid.uuid4().hex
    audio_path = WORK_DIR / f"{uid}{suffix}"
    midi_path = WORK_DIR / f"{uid}.mid"
    stem = Path(file.filename or "transcripcion").stem

    # Guardamos el audio subido en disco.
    with audio_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    # 0) (Opcional) Separar la voz de la mezcla con Demucs.
    to_transcribe = audio_path
    vocals_path = WORK_DIR / f"{uid}_vocals.wav"
    if separate_vocals:
        from backend.audio.separation import separate_vocals as extract_vocals

        try:
            extract_vocals(audio_path, vocals_path)
            to_transcribe = vocals_path
        except Exception as exc:  # noqa: BLE001
            audio_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Error al separar la voz: {exc}") from exc

    # 1) Audio → MIDI (siempre).
    try:
        transcribe_to_midi(to_transcribe, midi_path)
    except Exception as exc:  # noqa: BLE001 - queremos devolver el error al cliente
        raise HTTPException(status_code=500, detail=f"Error al transcribir: {exc}") from exc
    finally:
        audio_path.unlink(missing_ok=True)  # limpiamos el audio de entrada
        vocals_path.unlink(missing_ok=True)

    # 2) Devolver en el formato pedido.
    if format is OutputFormat.midi:
        return FileResponse(midi_path, media_type="audio/midi", filename=f"{stem}.mid")

    # MusicXML y PDF parten del MusicXML.
    from backend.musicxml.exporter import midi_to_musicxml

    xml_path = WORK_DIR / f"{uid}.musicxml"
    try:
        midi_to_musicxml(midi_path, xml_path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error al exportar MusicXML: {exc}") from exc

    if format is OutputFormat.musicxml:
        return FileResponse(
            xml_path,
            media_type="application/vnd.recordare.musicxml+xml",
            filename=f"{stem}.musicxml",
        )

    # format == pdf
    from backend.musicxml.pdf_exporter import (
        MuseScoreFailed,
        MuseScoreNotFound,
        musicxml_to_pdf,
    )

    pdf_path = WORK_DIR / f"{uid}.pdf"
    try:
        musicxml_to_pdf(xml_path, pdf_path)
    except MuseScoreNotFound as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MuseScoreFailed as exc:
        # Suele pasar al transcribir una mezcla completa (partitura densísima).
        raise HTTPException(
            status_code=422,
            detail=(
                "No se pudo grabar el PDF: la partitura es demasiado densa "
                "(probablemente audio polifónico). Activa 'Separar la voz primero' "
                "o usa un fragmento más corto. El MIDI y el MusicXML sí funcionan."
            ),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error al exportar PDF: {exc}") from exc
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{stem}.pdf")
