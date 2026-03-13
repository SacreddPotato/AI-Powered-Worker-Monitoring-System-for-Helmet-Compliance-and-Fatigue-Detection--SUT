---
title: SafeVision — AI Worker Safety
emoji: 👷
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: unlicense
---

# AI-Powered Worker Monitoring System

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-lightgrey?style=for-the-badge&logo=flask)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-orange?style=for-the-badge&logo=pytorch)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green?style=for-the-badge&logo=opencv)
![License](https://img.shields.io/badge/License-Unlicense-yellow.svg?style=for-the-badge)

**ML Models:** YOLOv8 (helmet/PPE), Swin Transformer (fatigue), dlib 68-point landmarks (EAR/MAR), with auto-download from HuggingFace

**Server:** Daphne (ASGI) serving both HTTP and WebSocket on a single port

## Features

- **Live Camera Feeds** — MJPEG streaming with annotated detection overlays, multi-camera grid with hero view
- **Real-time Alerts** — WebSocket-pushed alerts with severity levels, grouping by severity/camera/model/time
- **5 AI Models** — Helmet, fatigue, safety vest, gloves, goggles — each toggleable globally and per-camera
- **Developer Lab** — Upload videos for frame-by-frame analysis, threshold tuning, system performance monitoring
- **Fatigue Scoring** — Hybrid model: 60% Swin output, 30% EAR, 10% MAR with configurable thresholds

## Requirements

### System

- Python 3.10+
- Node.js 18+ (for frontend build)
- Conda (recommended, required for dlib)

### Python Dependencies

```
django>=5.0
djangorestframework
django-cors-headers
channels
daphne
opencv-python-headless
ultralytics
torch
torchvision
numpy
dlib
scipy
imutils
werkzeug
pillow
huggingface-hub
psutil
```

### Frontend Dependencies

Managed via `frontend/package.json` — React 18, Vite, Tailwind CSS v4, React Router.

## Quick Start

### 1. Clone and set up Python environment

```bash
git clone <repo-url>
cd AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT

# Create conda environment (recommended for dlib)
conda create -n fatigue_env python=3.10 -y
conda activate fatigue_env
conda install -c conda-forge dlib -y

pip install -r requirements.txt
```

### 2. Build the frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Initialize the database

```bash
cd backend
python manage.py migrate
cd ..
```

This creates `backend/monitoring.db` (SQLite) and seeds the 5 AI model settings.

### 4. Run the server

```bash
cd backend
daphne -b 0.0.0.0 -p 7860 sentinel.asgi:application
```

Open **http://localhost:7860** in your browser.

### Development Mode (hot reload)

The easiest way to develop is with the included run script, which launches both servers in one terminal:

```bash
python run.py
```

This starts Daphne (backend, port 7860) and Vite (frontend, port 5173) together. Open **http://localhost:5173** for hot-reload development. Press Ctrl+C to stop both.

You can also run them individually:

```bash
python run.py --backend   # backend only
python run.py --frontend  # frontend only
```

Or manually in separate terminals:

```bash
# Terminal 1
cd backend && daphne -b 0.0.0.0 -p 7860 sentinel.asgi:application

# Terminal 2
cd frontend && npm run dev
```

## Docker

```bash
docker build -t worker-monitor .
docker run -p 7860:7860 worker-monitor
```

The Dockerfile uses Miniconda, installs dlib via conda, builds the frontend, and runs Daphne on port 7860.

## API Reference

All endpoints are prefixed with `/api/v1/`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | Health check |
| GET/POST | `/cameras/` | List or create cameras |
| GET/PUT/DELETE | `/cameras/{id}/` | Camera CRUD |
| GET | `/cameras/{id}/status/` | Camera connection status |
| GET | `/cameras/{id}/stream/` | MJPEG stream (`?annotated=1` for overlays) |
| GET | `/models/` | List all model settings |
| PUT | `/models/{key}/` | Toggle model on/off |
| GET | `/cameras/{id}/models/` | Per-camera model overrides |
| PUT | `/cameras/{id}/models/{key}/` | Set per-camera model override |
| GET | `/alerts/` | List alerts (`?status=open&severity=high`) |
| PATCH | `/alerts/{id}/acknowledge/` | Acknowledge an alert |
| POST | `/detections/analyze/` | Trigger analysis for a camera |
| POST | `/dev/videos/` | Upload video (multipart, field: `video`) |
| GET | `/dev/videos/{id}/file/` | Download uploaded video |
| POST | `/dev/videos/{id}/analyze/` | Analyze video frames |
| GET/PUT | `/dev/thresholds/` | Get/set detection thresholds |
| GET | `/dev/performance/` | System performance metrics |

**WebSocket:** `ws://localhost:7860/ws/alerts/` — real-time alert push (JSON messages)

## ML Model Weights

Model weights are **not** checked into the repository. They are stored in `backend/ml_models/` and downloaded automatically from HuggingFace on first use. You can override download URLs with environment variables:

- `HELMET_MODEL_URL`
- `PPE_MULTI_MODEL_URL`
- `PERSON_MODEL_URL`
- `SHAPE_PREDICTOR_URL`

## Project Structure

```
backend/
├── sentinel/           # Django project (settings, urls, asgi)
├── cameras/            # Camera CRUD + MJPEG streaming
├── detection/          # Model settings, per-camera overrides, detection records
├── alerts/             # Alert model + WebSocket consumer
├── devlab/             # Video upload, analysis, threshold tuning
├── camera_service.py   # OpenCV camera capture service
├── inference_service.py# ML inference orchestrator
├── fatigue_engine.py   # Swin + dlib fatigue scoring
├── model_service.py    # Model loading + HuggingFace download
├── alerts_service.py   # Alert creation logic
├── config.py           # Runtime configuration
└── ml_models/          # Model weights (gitignored)

## 📄 License
This project is released under the **Unlicense License**.
