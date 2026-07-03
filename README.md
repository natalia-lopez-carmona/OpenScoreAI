# 🎼 OpenScoreAI

**Convierte audio musical en partituras editables (MusicXML, MIDI y PDF), 100% open source.**
Alternativa libre a Klangio, construida sobre modelos y librerías abiertas.

---

## ✨ Objetivo

Grabas o subes un audio → OpenScoreAI detecta las notas → genera **MIDI**, **MusicXML** y **PDF** de la partitura.

Pensado especialmente para **cantantes** que quieren transcribir su voz para practicar.

## 🧱 Arquitectura

```
OpenScoreAI/
├── backend/
│   ├── audio/          # Carga, normalización y pre-proceso de audio (librosa)
│   ├── transcription/  # Audio → notas (Basic Pitch; opcional Onsets & Frames)
│   ├── midi/           # Manejo de MIDI (pretty_midi)
│   ├── musicxml/       # Notas → MusicXML/PDF (music21)
│   ├── inference/      # Carga de modelos, gestión de GPU
│   └── api/            # API REST (FastAPI)
├── frontend/           # Interfaz web (pendiente de elegir stack)
├── ai_models/          # Pesos de modelos descargados (no versionados)
├── datasets/           # Datos de prueba/entrenamiento (no versionados)
├── tests/              # Pruebas (pytest)
└── docs/               # Documentación y decisiones de arquitectura
```

## 🚀 Puesta en marcha (desarrollo)

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. Instalar dependencias base (API)
pip install -r requirements.txt

# 3. Arrancar la API
uvicorn backend.api.main:app --reload

# 4. Abrir la documentación interactiva
# http://127.0.0.1:8000/docs
```

> ⚠️ Los modelos de transcripción (Basic Pitch, Demucs) son pesados y se instalan
> de forma **incremental**. Ver [docs/architecture.md](docs/architecture.md).

## 🗺️ Roadmap (MVP)

- [x] Estructura del proyecto y API base
- [ ] Endpoint `/transcribe`: audio → MIDI con **Basic Pitch**
- [ ] Exportar MIDI → **MusicXML** con music21
- [ ] Exportar **PDF** de la partitura
- [ ] (Opcional) Separar voz de la mezcla con **Demucs**
- [ ] Frontend web para subir audio y descargar partitura

## 📄 Licencia

MIT — ver [LICENSE](LICENSE). Libre para usar, modificar y compartir.
