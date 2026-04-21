---
title: SafeVision — AI Worker Safety
emoji: 👷
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
---

# AI-Powered Worker Monitoring System

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?style=flat-square&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-00FFFF?style=flat-square&logo=yolo&logoColor=black)
![Deep Learning](https://img.shields.io/badge/Deep_Learning-FF6F00?style=flat-square)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![Computer Vision](https://img.shields.io/badge/Computer_Vision-4CAF50?style=flat-square)
![WebSocket](https://img.shields.io/badge/WebSocket-010101?style=flat-square&logo=socketdotio&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-Unlicense-blue?style=flat-square)

Real-time worker safety monitoring dashboard with helmet compliance detection, fatigue analysis, and PPE verification. Built with Django + React.

## Architecture

```
┌────────────────────────────────────────────────────────┐
│  React SPA (Vite + Tailwind CSS v4)                    │
│  ┌──────┐ ┌────────┐ ┌────────┐ ┌─────────┐           │
│  │Feeds │ │ Alerts │ │ Models │ │ Dev Lab │           │
│  └──┬───┘ └───┬────┘ └───┬────┘ └────┬────┘           │
│     │    REST  │  WebSocket│     REST  │               │
└─────┼──────────┼──────────┼───────────┼────────────────┘
      │          │          │           │
┌─────┼──────────┼──────────┼───────────┼────────────────┐
│  Django (DRF + Channels via Daphne ASGI)               │
│  ┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────┐         │
│  │ cameras │ │ alerts │ │detection │ │devlab│         │
│  └────┬────┘ └───┬────┘ └─────┬────┘ └──┬───┘         │
│       │          │            │          │             │
│  ┌────┴──────────┴────────────┴──────────┴───────────┐ │
│  │  ML Services (camera, inference, fatigue engine)  │ │
│  │  YOLOv8 · Swin Transformer · dlib landmarks       │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

**Backend:** Django 5 + Django REST Framework + Django Channels (WebSocket for real-time alerts)

**Frontend:** React 18 + Vite + Tailwind CSS v4 — "Tactical HUD" dark theme with DM Sans / JetBrains Mono typography

**ML Models:** YOLOv8 (helmet/PPE), Swin Transformer (fatigue), dlib 68-point landmarks (EAR/MAR), versioned in-repo via Git LFS

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
psutil
openpyxl
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

# Fetch large model artifacts tracked by Git LFS
git lfs install
git lfs pull
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

Model weights are stored in `backend/ml_models/` and versioned with Git LFS.

If you clone the repo and see tiny pointer files or missing weights, run:

```bash
git lfs install
git lfs pull
```

Required files under `backend/ml_models/`:

- `best.pt`
- `yolov8n.pt`
- `swin_best.pth`
- `shape_predictor_68_face_landmarks.dat`
- `vest_detection.pt`
- `gloves_detection.pt`
- `goggles_detection.pt`
- `boots_detection.pt`
- `faceshield_detection.pt`
- `safety_suit_detection.pt`

### Upload or update model files with Git LFS

If you want to add/update weights directly in this repository (instead of runtime downloads), use Git LFS:

```bash
git lfs install
git lfs track "backend/ml_models/**"

# copy or replace model files in backend/ml_models/
git add .gitattributes backend/ml_models/
git commit -m "Add/update model weights via Git LFS"
git push
```

On a fresh clone, pull model binaries with:

```bash
git lfs pull
```

`python run.py` now validates required model files on startup and prints missing paths if any LFS asset is absent.

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
├── model_service.py    # Model loading and health state
├── alerts_service.py   # Alert creation logic
├── config.py           # Runtime configuration
└── ml_models/          # Model weights (tracked with Git LFS)

frontend/
├── src/
│   ├── pages/          # FeedsPage, AlertsPage, ModelsPage, DevLabPage
│   ├── components/     # CameraFeed, AlertCard, Badge, Toggle, Toast, IconRail
│   ├── api.js          # REST client
│   ├── ws.js           # WebSocket client with auto-reconnect
│   └── App.jsx         # Shell with routing + WebSocket connection
├── vite.config.js
└── tailwind.config.js
```

## License

See [LICENSE](LICENSE).
