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
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-010101?style=flat-square&logo=socketdotio&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-Unlicense-blue?style=flat-square)

Real-time worker safety monitoring dashboard with helmet compliance detection, fatigue analysis, and PPE verification. Built with Django + React.

## Architecture

```
┌────────────────────────────────────────────────────────┐
│  React SPA (Vite + Tailwind CSS)                      │
│  Feeds · Alerts · Models · Dev Lab                    │
└───────────────┬───────────────────────┬───────────────┘
                │ REST                  │ WebSocket
┌───────────────┴───────────────────────┴───────────────┐
│  Django (DRF + Channels + Daphne ASGI)               │
│  cameras · alerts · detection · devlab               │
└───────────────┬───────────────────────────────────────┘
                │
┌───────────────┴───────────────────────────────────────┐
│ ML Services: YOLOv8 · Swin Transformer · dlib         │
└────────────────────────────────────────────────────────┘
```

## Features

- Live camera feeds with WebSocket frame delivery and overlay annotations
- Real-time alerting with persisted SQLite storage
- 5 AI models: helmet, fatigue, vest, gloves, goggles
- Global and per-camera model toggles
- Alert exports:
  - Excel (`.xlsx`, with CSV fallback)
  - Pie-chart dataset + SVG chart export
- Date-range filtering for alerts (`today`, `week`, `month`, `custom`)
- Dev Lab for video upload, analysis, threshold tuning, and performance view

## Requirements

### System

- Python 3.10+
- Node.js 18+
- Conda recommended (especially for `dlib` on Windows)

### Python dependencies

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
openpyxl
```

Frontend dependencies are managed via `frontend/package.json`.

## Quick Start

### 1) Clone and create environment

```bash
git clone <repo-url>
cd AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT

conda create -n fatigue_env python=3.10 -y
conda activate fatigue_env
conda install -c conda-forge dlib -y
pip install -r requirements.txt
```

### 2) Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 3) Run in development

```bash
python run.py
```

`run.py` starts backend + frontend, and automatically runs Django migrations so the local SQLite database is created on first run.

- Frontend: http://localhost:5173
- Backend: http://localhost:7860

Optional:

```bash
python run.py --backend
python run.py --frontend
```

## Docker

```bash
docker build -t worker-monitor .
docker run -p 7860:7860 worker-monitor
```

## API Highlights

Base path: `/api/v1/`

- Cameras
  - `GET/POST /cameras/`
  - `GET/PUT/DELETE /cameras/{id}/`
  - `POST /cameras/probe/`
  - `GET /cameras/discover/`
  - `GET /cameras/{id}/status/`
- Models
  - `GET /models/`
  - `PUT /models/{key}/`
  - `GET /cameras/{id}/models/`
  - `PUT /cameras/{id}/models/{key}/`
  - `GET /cameras/models/overrides/`
- Alerts
  - `GET /alerts/`
  - `PATCH /alerts/{id}/acknowledge/`
  - `GET /alerts/export/excel/`
  - `GET /alerts/export/chart-data/?group_by=severity|camera|model|status|time`
  - date scope: `date_range=today|week|month|custom&start=YYYY-MM-DD&end=YYYY-MM-DD`
- Detections / Dev Lab
  - `POST /detections/analyze/`
  - `POST /dev/videos/`
  - `GET /dev/videos/{id}/file/`
  - `POST /dev/videos/{id}/analyze/`
  - `GET/PUT /dev/thresholds/`
  - `GET /dev/performance/`

WebSockets:

- `ws://localhost:7860/ws/alerts/`
- `ws://localhost:7860/ws/cameras/{camera_id}/stream/`

## ML Model Weights

Model weights are not checked into git. They are stored in `backend/ml_models/` and downloaded on demand.

Override URLs with env vars:

- `HELMET_MODEL_URL`
- `PPE_MULTI_MODEL_URL`
- `PERSON_MODEL_URL`
- `SHAPE_PREDICTOR_URL`

## Project Structure

```
backend/
├── sentinel/           # Django project (settings, urls, asgi)
├── cameras/            # Camera CRUD + streaming
├── detection/          # Model settings, overrides, detections
├── alerts/             # Alert persistence + websocket broadcasts
├── devlab/             # Video analysis + threshold tuning
├── inference_service.py
├── fatigue_engine.py
├── config.py
└── ml_models/          # Model weights (gitignored)

frontend/
├── src/
│   ├── pages/
│   ├── components/
│   ├── hooks/
│   ├── api.js
│   └── App.jsx
└── vite.config.js
```

## License

See [LICENSE](LICENSE).
