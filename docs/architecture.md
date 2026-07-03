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
- Usa **PyTorch** (aprovecha la GTX 1060).

### 3. Cuidado con el conflicto TensorFlow vs PyTorch
- Basic Pitch (TensorFlow/ONNX) y Demucs (PyTorch) pueden chocar en un mismo entorno.
- **Estrategia:** empezar solo con Basic Pitch. Añadir Demucs en un extra/env aparte
  si hace falta. Instalación **incremental**, no todo de golpe.

### 4. GPU (GTX 1060, 6 GB)
- Suficiente para Basic Pitch y para el modelo `htdemucs` de Demucs.
- Nota de rendimiento: revisar drivers CUDA para inferencia PyTorch.

## Pendiente de decidir
- **Frontend:** React/Vite vs algo más simple (HTMX, Streamlit para prototipo).
- **Exportación PDF:** music21 requiere MuseScore o LilyPond instalado para el PDF.
