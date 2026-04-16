# Sentinel Dashboard Overhaul — Design Spec

## Overview

Full UI/UX overhaul of the AI-Powered Worker Monitoring System. Migrating from Flask to Django (DRF + Channels) on the backend, rebuilding the React frontend with a "Tactical HUD" aesthetic, and adding real-time WebSocket alerts, flexible alert grouping, and a full-featured Developer Lab.

**Aesthetic direction:** Tactical HUD — dark zinc/slate palette (#09090b base), blue-violet accents, subtle grid textures, translucent alert panels. Feed-centric layout where camera streams dominate the viewport. Mockup approved: `.superpowers/brainstorm/full-mockup.html`

## Architecture

### Backend: Django + DRF + Channels

**Django apps:**

| App | Responsibility |
|-----|---------------|
| `core` | Project config, ASGI setup, URL routing, WebSocket routing |
| `cameras` | Camera CRUD, MJPEG streaming, status checks |
| `detection` | Inference service, ML model adapters (helmet, fatigue, PPE), model management |
| `alerts` | Alert CRUD, severity mapping, acknowledgment, WebSocket broadcast |
| `devlab` | Video upload, frame-sampled analysis, threshold tuning, performance profiling |

**Key decisions:**
- Django ORM with SQLite (migrated from raw SQL)
- Django REST Framework for all REST endpoints
- Django Channels + Redis channel layer for WebSocket real-time alerts
- Django Admin registered for all models as fallback management UI
- Conda environment `fatigue_env` for all Python dependencies
- Existing ML services (inference_service.py, fatigue_engine.py, camera_service.py) are preserved and wrapped by Django views/services — not rewritten

**Database models (Django ORM, replacing raw SQLite schema):**

- `Camera` — id, name, source_url, location (new field, nullable), is_active, created_at
- `ModelSetting` — key (unique), is_enabled. Display name, description, and file paths remain in `MODEL_DEFINITIONS` config dict (single source of truth)
- `CameraModel` — camera (FK), model_setting (FK), is_enabled (per-camera override)
- `Detection` — camera (FK), model_key, payload (JSONField), confidence, status (ok/error/unavailable), detected (boolean), created_at
- `Alert` — detection (FK), camera (FK), model_key, severity (high/medium/low), status (open/acknowledged), message, created_at, acknowledged_at
- `DevVideo` — id, original_filename, file_path, file_size, duration, uploaded_at (persisted to DB, not in-memory)

### Frontend: React + Vite + Tailwind CSS

- React 18 with React Router for client-side navigation
- Vite as bundler (already configured)
- Tailwind CSS for the Tactical HUD design system
- WebSocket client (native WebSocket API) for real-time alerts
- Component library: custom components, no external UI library

### Communication

| Channel | Protocol | Purpose |
|---------|----------|---------|
| REST | HTTP (DRF) | CRUD: cameras, models, detections, dev lab, alerts query |
| WebSocket | WS (Channels) | Real-time: alert push, camera status updates |
| MJPEG | HTTP stream | Live camera feeds (served by Django views) |

## Pages & Layout

### Global Layout
- **Icon rail** (56px, left edge): Logo, 4 nav icons (Feeds, Alerts, Models, Dev Lab), settings at bottom
- Active icon: blue highlight background
- Alert icon: red badge dot when unacknowledged alerts exist, pulses on critical
- **Toast notifications** (bottom-right): WebSocket-pushed alerts appear on any page, auto-dismiss after 8s

### Page 1: Feeds (default)

**Layout:** Camera grid (left, ~75%) + alert sidebar (right, 280px)

**Camera grid:**
- Hero camera spans full width (top row, 60% height)
- Secondary cameras in 2-column grid below
- Each camera shows: name, location, LIVE indicator, MJPEG stream, detection badge overlays (danger/warning/ok), active model tags
- Click camera to promote to hero position
- Subtle scan-line animation on hero feed

**Alert sidebar:**
- Grouped by severity (high, medium, low)
- Each alert: title, detail, camera source, relative timestamp
- Click alert to jump to Alerts page with detail panel open

### Page 2: Alerts

**Layout:** Alert table (left) + detail panel (right, 320px)

**Alert table:**
- Grouped sections with headers (severity by default)
- Each row: severity bar (color-coded), title, description, camera, timestamp, acknowledge button
- Grouping toggle: Severity | Camera | Model | Time (buttons in page header)

**Detail panel:**
- Shows selected alert's full info: source camera, model, detection details, confidence, timestamp
- JSON payload viewer (collapsible, monospace)
- Actions: Acknowledge, View Frame

### Page 3: Models

**Layout:** Single scrollable page

**Global model settings:**
- Card grid (auto-fill, min 220px)
- Each card: model name, status badge (Active/Disabled), description, latency, threshold, toggle switch

**Per-camera overrides:**
- Table: rows = cameras, columns = models
- Each cell: small toggle switch
- Camera online/offline dot indicator

### Page 4: Dev Lab

**Layout:** Sub-tabs (top) + split panel (left controls, right preview/results)

**Sub-tabs:**
1. **Video Analysis** — Upload zone, analysis config (sample rate, max samples, context), run analysis, view results
2. **Live Camera Test** — Select camera IP, run models in real-time with debug overlays, confidence readouts, per-frame detection logs
3. **Threshold Tuning** — Interactive sliders for: confidence threshold, consecutive frames, EAR threshold, MAR threshold, head tilt degrees. Live preview shows effect on current frame/video
4. **Performance** — FPS, inference latency per model, GPU utilization, memory usage. Real-time updating cards

**Left panel (controls):**
- Video upload drop zone
- Analysis configuration fields
- Threshold sliders with current values
- Execution log (monospace, timestamped, color-coded by level)

**Right panel (results):**
- Video preview (Raw / Annotated / Side-by-side toggle)
- Performance metrics grid (FPS, latency, GPU, memory)
- Detection summary table
- Model comparison table

## Real-Time Alerts (WebSocket)

**Flow:**
1. Detection loop runs on backend (per-camera, per-enabled-model)
2. When alert-worthy detection occurs, alert is saved to DB
3. Alert is broadcast via Django Channels to all connected WebSocket clients
4. Frontend receives alert, updates: alert sidebar (Feeds page), alert table (Alerts page), toast notification (any page), icon badge count

**WebSocket message format:**
```json
{
  "type": "alert.new",
  "alert": {
    "id": 42,
    "severity": "high",
    "model_key": "helmet",
    "camera_id": 1,
    "camera_name": "Camera 01 — Warehouse A",
    "message": "No helmet detected — 2 workers",
    "payload": {...},
    "created_at": "2026-03-12T14:32:05.421Z"
  }
}
```

**Additional WS events:**
- `alert.acknowledged` — when someone acknowledges an alert
- `camera.status` — camera online/offline changes
- `detection.result` — per-frame detection summary for active camera feeds (used to update badge overlays without relying solely on MJPEG annotations)

## Alert Grouping

Frontend-driven grouping with 4 modes (toggle buttons):
- **Severity** (default): High > Medium > Low sections
- **Camera**: Group by camera source, each camera is a collapsible section
- **Model**: Group by detection model (helmet, fatigue, vest, etc.)
- **Time**: Cluster alerts within time windows (last minute, last 5 min, last hour, older)

## API Endpoints (DRF)

Preserving the existing API contract where possible, namespaced under `/api/v1/`:

**Cameras:** GET/POST `/cameras/`, GET/PUT/DELETE `/cameras/{id}/`, GET `/cameras/{id}/status/`, GET `/cameras/{id}/stream/`

**Models:** GET `/models/`, PUT `/models/{key}/`, GET `/cameras/{id}/models/`, PUT `/cameras/{id}/models/{key}/`

**Detections:** POST `/detections/analyze/`, GET `/detections/`

**Alerts:** GET `/alerts/` (supports `?limit=N&offset=N` pagination), PATCH `/alerts/{id}/acknowledge/`

**Dev Lab:** POST `/dev/videos/`, GET `/dev/videos/{id}/file/`, GET `/dev/videos/{id}/stream/`, POST `/dev/videos/{id}/analyze/`, GET `/dev/performance/` (returns FPS, latency per model, GPU %, memory usage), GET/PUT `/dev/thresholds/` (read/update confidence, EAR, MAR, consecutive frames, head tilt values)

**Health:** GET `/health/`

**WebSocket:** `ws://host/ws/alerts/`

**Notes:**
- Auth is out of scope for this phase (matches existing Flask app — no auth)
- Dev Lab "Live Camera Test" tab reuses the existing `/cameras/{id}/stream/?annotated=1` endpoint with the threshold overrides applied
- All list endpoints support `?limit=N&offset=N` pagination (default limit: 100, max: 500)

## Design System (Tailwind)

**Colors (CSS variables + Tailwind config):**
- Base: zinc-950 (#09090b)
- Surface: zinc-900 (#18181b)
- Border: zinc-800 (#27272a)
- Text primary: zinc-50 (#fafafa)
- Text secondary: zinc-400 (#a1a1aa)
- Text muted: zinc-500 (#71717a)
- Accent: blue-500 (#3b82f6) / violet-500 (#8b5cf6)
- Danger: red-500 (#ef4444)
- Warning: amber-500 (#f59e0b)
- Success: green-500 (#22c55e)

**Typography:**
- Body: DM Sans (Google Fonts)
- Mono: JetBrains Mono (logs, JSON, technical values)

**Component patterns:**
- Cards: bg-zinc-900, border border-zinc-800, rounded-lg
- Badges: translucent colored backgrounds with colored borders
- Toggles: custom switch component (36x20px)
- Alert severity bars: 4px left border, color-coded

## What We're NOT Changing

- ML model files and weights (kept in backend/ml_models/)
- Inference logic (inference_service.py, fatigue_engine.py core algorithms)
- Camera streaming approach (MJPEG)
- HuggingFace/GitHub auto-download for model weights
- SQLite as the database engine (just using Django ORM instead of raw SQL)

## Environment

- Python: conda environment `fatigue_env`
- Node: existing setup, Vite bundler
- Docker: update Dockerfile for Django + Daphne (ASGI server for HTTP + WebSocket)
- Redis: use Django Channels **InMemoryChannelLayer** for dev/single-machine. Redis optional for multi-process production — not required this phase
