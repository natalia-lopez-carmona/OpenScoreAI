"""Separación de fuentes con Demucs: extraer la voz de una mezcla.

Útil para transcribir la línea vocal de una canción completa: primero aislamos
la voz del resto de instrumentos, y luego esa voz limpia va al transcriptor.

Usa la GPU (CUDA) si está disponible; si no, cae a CPU automáticamente.
"""
from __future__ import annotations

from pathlib import Path

# Cargar el modelo de Demucs es costoso; lo reutilizamos (singleton perezoso).
_model = None
_device = None


def _get_model():
    """Carga (una sola vez) el modelo htdemucs y elige dispositivo."""
    global _model, _device
    if _model is None:
        import torch
        from demucs.pretrained import get_model

        _device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = get_model("htdemucs")
        _model.to(_device)
        _model.eval()
    return _model, _device


def separate_vocals(audio_path: str | Path, output_path: str | Path) -> Path:
    """Extrae la pista de voz de un audio y la guarda como WAV.

    Args:
        audio_path: audio de entrada (mezcla).
        output_path: ruta donde se guardará la voz aislada (.wav).

    Returns:
        La ruta del archivo de voz generado.
    """
    import torch
    from demucs.apply import apply_model
    from demucs.audio import AudioFile, save_audio

    audio_path = Path(audio_path)
    output_path = Path(output_path)

    model, device = _get_model()

    # Cargamos el audio al sample rate y nº de canales que espera el modelo.
    wav = AudioFile(str(audio_path)).read(
        streams=0, samplerate=model.samplerate, channels=model.audio_channels
    )
    # Normalización estándar de Demucs (con guarda ante audio silencioso).
    ref = wav.mean(0)
    std = ref.std() + 1e-8
    wav = (wav - ref.mean()) / std

    with torch.no_grad():
        sources = apply_model(model, wav[None], device=device, progress=False)[0]
    sources = sources * std + ref.mean()

    # Seleccionamos la pista "vocals" (htdemucs: drums, bass, other, vocals).
    vocals = sources[model.sources.index("vocals")]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_audio(vocals, str(output_path), model.samplerate)
    return output_path
