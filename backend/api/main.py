"""OpenScoreAI — API REST (FastAPI).

Punto de entrada de la aplicación. Arranca con:
    uvicorn backend.api.main:app --reload
"""
from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

app = FastAPI(
    title="OpenScoreAI",
    description="Convierte audio musical en partituras editables (MIDI, MusicXML, PDF).",
    version="0.1.0",
)

# Formatos de audio aceptados.
ALLOWED_AUDIO = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}

# Carpeta temporal para audios subidos y MIDIs generados.
WORK_DIR = Path(tempfile.gettempdir()) / "openscoreai"
WORK_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Comprobación de vida del servicio."""
    return {"status": "ok", "service": "OpenScoreAI", "version": "0.1.0"}


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    """Mensaje de bienvenida y enlace a la documentación."""
    return {"message": "OpenScoreAI está en marcha 🎼", "docs": "/docs"}


@app.post("/transcribe", tags=["transcription"])
def transcribe(file: UploadFile = File(...)) -> FileResponse:
    """Recibe un audio y devuelve su transcripción como archivo MIDI.

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

    # Guardamos el audio subido en disco.
    with audio_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    # Transcribimos.
    try:
        transcribe_to_midi(audio_path, midi_path)
    except Exception as exc:  # noqa: BLE001 - queremos devolver el error al cliente
        raise HTTPException(status_code=500, detail=f"Error al transcribir: {exc}") from exc
    finally:
        audio_path.unlink(missing_ok=True)  # limpiamos el audio de entrada

    download_name = f"{Path(file.filename or 'transcripcion').stem}.mid"
    return FileResponse(midi_path, media_type="audio/midi", filename=download_name)
