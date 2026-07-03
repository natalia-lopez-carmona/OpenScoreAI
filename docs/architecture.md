# Arquitectura y decisiones de OpenScoreAI

## Pipeline principal

```
Audio (wav/mp3)
   │
   ▼
[audio]        carga + normaliza (librosa)
   │
   ▼
[transcription]  audio → notas (Basic Pitch)      ← motor principal
   │
   ▼
[midi]         notas → MIDI (pretty_midi)
   │
   ▼
[musicxml]     MIDI → MusicXML + PDF (music21)
   │
   ▼
Partitura editable
```

## Decisiones de arquitectura

### 1. Motor de transcripción: **Basic Pitch** primero
- **Por qué:** `pip install basic-pitch`, funciona ya, es **polifónico**, ligero y
  con buenos resultados en voz. Perfecto para el caso de uso (cantante).
- **Onsets & Frames** queda como opción futura, pero está orientado a **piano** y
  su implementación de referencia (Magenta) usa TensorFlow antiguo → más fricción.

### 2. Demucs es **opcional**
- Solo se necesita si el audio es una **mezcla** y hay que **aislar la voz** antes
  de transcribir. Para grabaciones de voz limpia, se salta este paso.
- Usa **PyTorch con CUDA** (aprovecha la GTX 1060): separa un clip en segundos.
- Implementado en `backend/audio/separation.py` con la API de bajo nivel de Demucs
  (`get_model` + `apply_model`), modelo **htdemucs**, singleton perezoso.
- Se activa con `separate_vocals=true` en `/transcribe` o el interruptor del frontend.

### 3. Cuidado con el conflicto TensorFlow vs PyTorch
- Basic Pitch (TensorFlow/ONNX) y Demucs (PyTorch) pueden chocar en un mismo entorno.
- **Estrategia:** empezar solo con Basic Pitch. Añadir Demucs en un extra/env aparte
  si hace falta. Instalación **incremental**, no todo de golpe.

### 4. GPU (GTX 1060, 6 GB)
- Suficiente para Basic Pitch y para el modelo `htdemucs` de Demucs.
- Nota de rendimiento: revisar drivers CUDA para inferencia PyTorch.

### 5. Exportación a PDF: **MuseScore CLI** (decidido)
- El PDF se genera llamando **directamente al ejecutable de MuseScore 4**
  (`backend/musicxml/pdf_exporter.py`), no por la ruta interna de music21 (más frágil).
- Flujo: MIDI → MusicXML (music21) → PDF (MuseScore).
- MuseScore se autodetecta; se puede forzar con `MUSESCORE_PATH`.
- Si no está instalado, el endpoint responde **503** (MIDI y MusicXML siguen funcionando).

## Pendiente de decidir
- **Frontend:** React/Vite vs algo más simple (HTMX, Streamlit para prototipo).
- **Cuantización rítmica:** mejorar la limpieza de figuras (actualmente `quantize()` básico).
