# Worker Monitoring Admin Dashboard (Refactor)

This branch refactors the legacy fatigue/helmet demo app into an admin dashboard architecture:

- **Backend:** Flask REST API (`backend/app.py`)
- **Frontend:** React/Vite app scaffold (`frontend/`); build output is generated into `frontend/dist/`
- **Persistence:** SQLite (`backend/monitoring.db`, runtime-generated)
- **Core features:**
  - Multi-camera inventory with IP/RTSP/custom sources
  - Camera wall streaming (`/api/v1/cameras/<id>/stream`)
  - Per-camera and global AI model toggles
  - Alerts feed and acknowledgment workflow
  - Model adapters: **helmet**, **fatigue**, **vest**, **gloves**, **goggles**
  - Model storage refactored to `backend/ml_models/` (auto-migrates restored legacy model files on startup)
  - Vest detection includes QR scan extraction (`vest_id`) when a QR is visible
  - Fullscreen midnight-purple dark-mode dashboard UI with left drawer navigation and gradient accents
  - Dev video debugging flow (upload video, then analyze sampled frames through enabled models)

## API Overview

- `GET /api/v1/health`
- `GET/POST /api/v1/cameras`
- `GET/PUT/DELETE /api/v1/cameras/<id>`
- `GET /api/v1/cameras/<id>/status`
- `GET /api/v1/cameras/<id>/stream`
- `GET /api/v1/cameras/<id>/stream?annotated=1` (live boxes/pose overlays)
- `GET /api/v1/models`
- `PUT /api/v1/models/<model_key>`
- `GET /api/v1/cameras/<id>/models`
- `PUT /api/v1/cameras/<id>/models/<model_key>`
- `POST /api/v1/detections/analyze`
- `GET /api/v1/detections`
- `GET /api/v1/alerts`
- `PATCH /api/v1/alerts/<id>/acknowledge`
- `POST /api/v1/dev/videos` (multipart upload field: `file`)
- `GET /api/v1/dev/videos/<video_id>/file`
- `GET /api/v1/dev/videos/<video_id>/stream`
- `GET /api/v1/dev/videos/<video_id>/stream?annotated=1` (debug overlay stream)
- `POST /api/v1/dev/videos/<video_id>/analyze`

## Running

### Backend

```bash
python backend/app.py
```

Backend serves API on `http://localhost:7860` and serves frontend static assets from `frontend/dist`.

### Frontend (React/Vite scaffold)

```bash
cd frontend
npm install
npm run dev
```

For production build:

```bash
npm run build
```

## Notes

- The obsolete Fatigue V2 model path has been removed from runtime.
- New PPE model adapters attempt automatic model download when weights are missing.
- Fatigue scoring uses hybrid logic:
  - 60% Swin model output
  - 30% EAR score
  - 10% MAR score
- Fatigue alert rules:
  - sustained fatigue over consecutive frames (default threshold: 8)
  - head tilt is included in telemetry/trigger_reason (informational), while alert classification follows sustained hybrid fatigue
- Overlay-driven debugging:
  - live and dev streams can render model boxes and fatigue landmarks/pose lines
  - alerts now map to visible evidence in annotated streams
- Open-source download sources are configurable via environment variables:
  - `HELMET_MODEL_URL`
  - `PPE_MULTI_MODEL_URL`
  - `PERSON_MODEL_URL`
  - `SHAPE_PREDICTOR_URL`
- On startup, model files are expected in `backend/ml_models` and legacy files in `backend/` are auto-migrated.
- If download still fails, API responds with explicit `status: "unavailable"` and detailed load/download errors.
