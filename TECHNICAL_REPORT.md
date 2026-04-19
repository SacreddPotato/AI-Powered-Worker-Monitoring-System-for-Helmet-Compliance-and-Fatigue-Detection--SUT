# Technical Report: AI-Powered Worker Monitoring System

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Machine Learning Pipeline](#2-machine-learning-pipeline)
   - 2.1 [Helmet Detection (YOLOv8)](#21-helmet-detection-yolov8)
   - 2.2 [PPE Detection (YOLOv8)](#22-ppe-detection-yolov8)
   - 2.3 [Fatigue Detection (SwinV2-S + dlib)](#23-fatigue-detection-swinv2-s--dlib)
   - 2.4 [Annotation Rendering](#24-annotation-rendering)
    - 2.5 [Model Selection Rationale](#25-model-selection-rationale)
3. [Backend Architecture](#3-backend-architecture)
   - 3.1 [Django Configuration](#31-django-configuration)
   - 3.2 [ASGI & WebSocket Routing](#32-asgi--websocket-routing)
   - 3.3 [Database Schema](#33-database-schema)
   - 3.4 [Django Applications](#34-django-applications)
   - 3.5 [REST API Reference](#35-rest-api-reference)
    - 3.6 [API Usage Matrix](#36-api-usage-matrix)
4. [Frontend Architecture](#4-frontend-architecture)
   - 4.1 [Application Structure](#41-application-structure)
   - 4.2 [Pages](#42-pages)
   - 4.3 [Shared Components](#43-shared-components)
   - 4.4 [State Management](#44-state-management)
   - 4.5 [WebSocket Client](#45-websocket-client)
5. [Real-Time Data Flow](#5-real-time-data-flow)
6. [Configuration & Thresholds](#6-configuration--thresholds)
7. [Deployment](#7-deployment)

---

## 1. System Overview

**SafeVision AI** is a real-time worker safety monitoring system that uses computer vision and deep learning to detect helmet compliance, PPE violations, and worker fatigue from IP camera feeds. The current stack supports eight detection model keys (`helmet`, `fatigue`, `vest`, `gloves`, `goggles`, `boots`, `faceshield`, `safetysuit`) with per-camera enablement, per-camera severity policy, and real-time alerting.

The dashboard includes live monitoring, alert center analytics, model/severity management, and a developer lab for controlled video and threshold testing. It is designed for low-latency inference with practical operations controls rather than offline-only batch workflows.

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | Django 5.x + Django REST Framework | REST API, ORM, admin |
| **ASGI Server** | Daphne | Serves HTTP and WebSocket on a single port |
| **WebSocket** | Django Channels (InMemoryChannelLayer) | Real-time alert push, camera binary frame streaming, live video analysis streaming |
| **Object Detection** | YOLOv8n (Ultralytics) | Helmet and PPE detection (vest, gloves, goggles, boots, faceshield, safetysuit) |
| **Fatigue Model** | Swin Vision Transformer v2-Small | Drowsiness classification from face patches |
| **Facial Landmarks** | dlib 68-point shape predictor | EAR/MAR computation, head pose estimation |
| **Feature Assist** | MediaPipe Hands / Face Mesh | Robust glove/goggle absence estimation when explicit `no_*` classes are weak |
| **Computer Vision** | OpenCV | Frame capture, image processing, head pose via PnP |
| **Frontend Framework** | React 18 | Single-page application |
| **Build Tool** | Vite 5 | Development server, production bundling |
| **Styling** | Tailwind CSS v4 | Utility-first dark theme ("Tactical HUD") |
| **Routing** | React Router v7 | Client-side navigation |
| **Database** | SQLite | Lightweight, file-based persistence |
| **ML Framework** | PyTorch + Ultralytics | Model inference and weight loading |
| **Model Distribution** | HuggingFace Hub | Automatic weight download on first run |

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  React 18 SPA (Vite + Tailwind CSS v4)                       │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌────────────────┐ │
│  │  Feeds   │ │  Alerts   │ │  Models  │ │   Dev Lab      │ │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └───────┬────────┘ │
│       │    REST      │  WebSocket │      REST      │          │
└───────┼──────────────┼───────────┼────────────────┼──────────┘
        │              │           │                │
┌───────┼──────────────┼───────────┼────────────────┼──────────┐
│  Django 5 (DRF + Channels via Daphne ASGI)                   │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌───────────────┐ │
│  │ cameras  │ │  alerts  │ │ detection  │ │    devlab     │ │
│  └────┬─────┘ └────┬─────┘ └──────┬─────┘ └──────┬────────┘ │
│       └─────────────┴──────────────┴──────────────┘          │
│                            │                                  │
│  ┌─────────────────────────┴────────────────────────────────┐│
│  │  ML Inference Service                                     ││
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────────────┐ ││
│  │  │ YOLOv8n     │ │ SwinV2-Small │ │ dlib 68-landmarks  │ ││
│  │  │ (Helmet/PPE)│ │ (Fatigue)    │ │ (EAR/MAR/Pose)     │ ││
│  │  └─────────────┘ └──────────────┘ └────────────────────┘ ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Machine Learning Pipeline

The system runs **eight detection model keys** — helmet, fatigue, vest, gloves, goggles, boots, faceshield, and safetysuit. Models are independently toggleable per-camera, loaded lazily on first use, and support automatic download where URLs are configured.

### Why this model stack?

- **YOLOv8n for PPE:** chosen for strong real-time throughput on CPU/GPU with simple deployment; compared to heavier detectors, it gives lower latency and easier operational tuning.
- **SwinV2-S + dlib for fatigue:** chosen over a pure detector because fatigue is temporal/physiological; combining deep features with EAR/MAR and head pose improves robustness and interpretability.
- **Hybrid architecture:** keeps mission-critical alerts explainable (landmark metrics + trigger reasons) while retaining modern model accuracy.

### 2.1 Helmet Detection (YOLOv8)

#### Model Architecture

| Property | Value |
|----------|-------|
| **Architecture** | YOLOv8n (nano variant) |
| **Source** | `keremberke/yolov8n-hard-hat-detection` on HuggingFace |
| **Input** | BGR image frame (any resolution, YOLO resizes internally) |
| **Inference Confidence** | 0.35 |
| **Task** | Hard hat presence/absence detection |

#### Two-Stage Detection Pipeline

Helmet detection uses a **dual-model pipeline** that combines a helmet-specific YOLOv8 model with a standard COCO person detector:

**Stage 1 — Person Detection:**
A standard YOLOv8n model (pretrained on COCO) detects all persons in the frame, filtering for class 0 (person) with confidence ≥ 0.35.

**Stage 2 — Helmet Detection:**
The helmet-specific YOLOv8n model runs on the same frame, producing bounding boxes for helmets and hard hats.

**Stage 3 — IoU-Based Matching:**
Each detected person is checked against all helmet detections using Intersection over Union (IoU):

```
For each person box:
    head_region = upper 38% of person bounding box
    has_helmet = False

    For each helmet box:
        if IoU(person_box, helmet_box) > 0.02:     # body overlap
            has_helmet = True
        if IoU(head_region, helmet_box) > 0.08:     # head overlap
            has_helmet = True

    if not has_helmet:
        → label "helmet missing" (red box)
    else:
        → label "helmet" (green box)
```

The dual-threshold IoU approach (2% body, 8% head) prevents false negatives when helmets are above the worker's head or at unusual angles.

#### Output Format

```json
{
  "status": "ok",
  "detected": true,
  "confidence": 0.92,
  "payload": {
    "person_count": 3,
    "helmet_count": 2,
    "no_helmet_count": 1,
    "classification": "helmet_missing",
    "boxes": [
      {"x1": 100, "y1": 50, "x2": 200, "y2": 150, "label": "helmet", "color": "green"},
      {"x1": 300, "y1": 80, "x2": 450, "y2": 400, "label": "worker", "color": "blue"},
      {"x1": 500, "y1": 60, "x2": 600, "y2": 350, "label": "helmet missing", "color": "red"}
    ]
  }
}
```

### 2.2 PPE Detection (YOLOv8)

#### Model Architecture

| Property | Value |
|----------|-------|
| **Architecture** | YOLOv8n (nano variant) |
| **Source** | `Tanishjain9/yolov8n-ppe-detection-6classes` on HuggingFace |
| **Input** | BGR image frame |
| **Inference Confidence** | 0.35 |
| **Task** | Multi-class PPE detection (vest, gloves, goggles, boots, faceshield, safetysuit) |

PPE adapters use YOLOv8 with model-specific target label filtering and shared post-processing logic:

| Model | Target Labels | Missing Labels |
|-------|--------------|----------------|
| **Vest** | vest, safety vest, safety_vest | — |
| **Gloves** | glove, gloves | no_glove, no-glove |
| **Goggles** | goggles, goggle | no_goggles, no-goggles |
| **Boots** | boot, boots, safety boot | no_boot, no-boots |
| **Face Shield** | face shield, faceshield, shield | no_face_shield, no shield |
| **Safety Suit** | safety suit, safetysuit, coverall | no_safety_suit |

#### Detection Logic

1. Run YOLO inference on the full frame
2. Normalize all detected class names (strip underscores/dashes, lowercase)
3. Match detections against the model's target labels
4. Labels starting with "no " or "without " are flagged as missing items
5. Classification: `ppe_missing` if any missing items, `ppe_ok` if all present

#### Vest QR Code Extraction

The vest adapter has an additional QR code detection step:
- Uses OpenCV's `QRCodeDetector` to read QR codes within detected vest bounding boxes
- Falls back to scanning the full frame if no QR found in the box
- Extracted data is stored as `vest_id` in the payload for worker identification

#### Why YOLOv8 for PPE instead of alternatives?

- **Operational simplicity:** single framework (Ultralytics) for loading, inference, class metadata, and deployment.
- **Latency advantage:** `YOLOv8n` is fast enough for multi-camera live overlays with periodic inference.
- **Adaptability:** class-name driven filtering lets one engine support multiple PPE policies without custom post-training code per endpoint.

#### Output Format

```json
{
  "status": "ok",
  "detected": true,
  "confidence": 0.88,
  "payload": {
    "count": 4,
    "missing_count": 1,
    "ok_count": 3,
    "classification": "ppe_missing",
    "boxes": [
      {"x1": 100, "y1": 200, "x2": 300, "y2": 500, "label": "vest", "color": "green"},
      {"x1": 150, "y1": 300, "x2": 250, "y2": 400, "label": "no_glove", "color": "red"}
    ],
    "vest_id": "WKR-0042"
  }
}
```

### 2.3 Fatigue Detection (SwinV2-S + dlib)

Fatigue detection is the most complex model in the system, combining a deep learning vision transformer with classical computer vision techniques in a **hybrid scoring pipeline**.

#### Why SwinV2 + landmarks instead of a single detector?

- **Temporal fatigue cues** (eye closure patterns, yawning, nodding) are better captured with hybrid reasoning than object boxes alone.
- **Interpretability:** EAR/MAR/tilt metrics are inspectable and tunable in DevLab, which is hard with opaque-only classifiers.
- **Stability:** consecutive-frame thresholds reduce transient false alerts from blinks or brief expression changes.

#### Model Architecture

| Property | Value |
|----------|-------|
| **Architecture** | Swin Vision Transformer v2-Small |
| **Head** | `nn.Dropout(0.5) → nn.Linear(768, 1)` with sigmoid |
| **Input** | 224×224 RGB face patch, ImageNet-normalized |
| **Output** | Single float [0, 1] — fatigue probability |
| **Weights** | `swin_best.pth` (custom trained) |

#### Face Detection & Landmark Extraction

**dlib Face Detector:**
- `dlib.get_frontal_face_detector()` — HOG-based frontal face detector
- Detects the largest face in the frame
- Pads the face region by ±12 pixels for context

**68-Point Shape Predictor:**
- `shape_predictor_68_face_landmarks.dat` (downloaded from dlib-models)
- Extracts 68 facial landmarks organized into regions:
  - Points 0–16: Jawline
  - Points 17–26: Eyebrows
  - Points 27–35: Nose
  - Points 36–41: Left eye
  - Points 42–47: Right eye
  - Points 48–59: Outer mouth
  - Points 60–67: Inner mouth

#### Eye Aspect Ratio (EAR)

The Eye Aspect Ratio measures eye openness. A low EAR indicates closed or drooping eyes:

```
        ||P2 - P6|| + ||P3 - P5||
EAR = ─────────────────────────────
              2 × ||P1 - P4||

Where P1-P6 are the 6 landmarks of each eye.
```

The EAR is computed for both eyes and averaged. The normalized EAR score is:

```
ear_score = clamp((0.28 - EAR) / 0.28, 0, 1)
```

When EAR drops below 0.28 (eyes closing), `ear_score` increases toward 1.0.

#### Mouth Aspect Ratio (MAR)

The Mouth Aspect Ratio detects yawning — an open mouth produces a high MAR:

```
        ||P2 - P8|| + ||P3 - P7|| + ||P4 - P6||
MAR = ───────────────────────────────────────────
                    3 × ||P1 - P5||

Where P1-P8 are the 8 inner mouth landmarks (indices 60-67).
```

The normalized MAR score is:

```
mar_score = clamp((MAR - 0.6) / (1.0 - 0.6), 0, 1)
```

When MAR exceeds 0.6 (mouth opening/yawning), `mar_score` increases toward 1.0.

#### Head Pose Estimation

Head pose is estimated using OpenCV's Perspective-n-Point (PnP) solver:

**3D Model Points** (canonical face geometry):
| Point | 3D Coordinates (mm) |
|-------|---------------------|
| Nose tip | (0, 0, 0) |
| Chin | (0, −63.6, −12.5) |
| Left eye corner | (−43.3, 32.7, −26.0) |
| Right eye corner | (43.3, 32.7, −26.0) |
| Mouth left | (−28.9, −28.9, −24.1) |
| Mouth right | (28.9, −28.9, −24.1) |

**Camera Matrix:**
```
focal_length = frame_width / (2 × tan(30°))

        ┌ focal_length    0        center_x ┐
K =     │      0      focal_length  center_y │
        └      0          0            1     ┘
```

**PnP Solution:**
```python
success, rotation_vec, translation_vec = cv2.solvePnP(
    model_points_3d, image_points, camera_matrix,
    dist_coeffs=np.zeros((4, 1)),
    flags=cv2.SOLVEPNP_ITERATIVE
)
```

The rotation vector is converted to Euler angles (pitch, yaw, roll). Head tilt is defined as `max(|pitch|, |roll|)`.

#### Hybrid Fatigue Score

The final fatigue decision combines three signals with fixed weights:

```
hybrid_score = 0.6 × ml_probability + 0.3 × ear_score + 0.1 × mar_score
```

| Component | Weight | Source | Measures |
|-----------|--------|--------|----------|
| ML Probability | 60% | SwinV2-S sigmoid output | Visual drowsiness patterns |
| EAR Score | 30% | dlib landmarks | Eye closure |
| MAR Score | 10% | dlib landmarks | Yawning |

**Decision Logic:**
```
is_fatigued = hybrid_score ≥ 0.55
```

#### Consecutive Frame Tracking

To prevent false alarms from momentary blinks or expressions, the system requires **8 consecutive frames** with `is_fatigued = True` before triggering an alert:

```
if is_fatigued:
    consecutive_count += 1
else:
    consecutive_count = 0

alert_triggered = consecutive_count ≥ 8
```

An independent head tilt check also triggers if `max(|pitch|, |roll|) > 15°` (potential nodding off).

#### Output Format

```json
{
  "status": "ok",
  "detected": true,
  "confidence": 0.72,
  "payload": {
    "fatigue_probability": 0.68,
    "ear": 0.19,
    "mar": 0.45,
    "ear_score": 0.32,
    "mar_score": 0.0,
    "hybrid_score": 0.72,
    "head_tilt_degrees": 8.3,
    "head_pitch": -5.2,
    "head_yaw": 3.1,
    "head_roll": 8.3,
    "head_tilt_exceeded": false,
    "is_fatigued": true,
    "consecutive_fatigue_frames": 12,
    "fatigue_frame_threshold": 8,
    "trigger_reason": ["sustained_fatigue"],
    "face_box": {"x1": 340, "y1": 120, "x2": 520, "y2": 340},
    "landmarks": [[345, 230], [348, 245], ...],
    "pose_line": {"start": [430, 200], "end": [425, 140]}
  }
}
```

### 2.4 Annotation Rendering

The annotation module (`annotation.py`) draws detection results onto video frames using OpenCV:

**PPE Models** (helmet, vest, gloves, goggles, boots, faceshield, safetysuit):
- Colored bounding boxes with labels and confidence percentages
- Red boxes for missing items, green for compliant items

**Fatigue Model:**
- Face bounding box (red if fatigued, orange if alert)
- 68 facial landmarks as small circles
- Head pose arrow (cyan) from nose tip indicating orientation
- Metrics text overlay: EAR value, MAR value, head tilt degrees

**Model Color Scheme:**

| Model | Color (BGR) | Hex |
|-------|-------------|-----|
| Helmet | (0, 200, 80) | Green |
| Fatigue | (0, 140, 255) | Orange |
| Vest | (255, 160, 50) | Blue |
| Gloves | (0, 220, 255) | Yellow |
| Goggles | (220, 200, 0) | Cyan |
| Boots | (0, 220, 255) | Yellow |
| Face Shield | (220, 200, 0) | Cyan |
| Safety Suit | (255, 160, 50) | Blue |

### 2.5 Model Selection Rationale

| Model Key | Technology | Why chosen | Advantage in this system |
|-----------|------------|------------|--------------------------|
| `helmet` | YOLOv8n + YOLOv8n person model | Helmet-only classes often miss context; dual-stage matching improves compliance reasoning | Better missing-helmet inference at low latency |
| `vest` | YOLOv8n PPE adapter + OpenCV QR detector | Single detector with lightweight post-processing is operationally simple | Real-time detection + optional worker ID extraction |
| `gloves` | YOLOv8n PPE adapter + MediaPipe Hands assist | Gloves can be tiny/occluded; explicit `no_*` labels are inconsistent | More robust missing-glove estimation on noisy feeds |
| `goggles` | YOLOv8n PPE adapter + MediaPipe Face Mesh assist | Eye PPE classes can be unstable at distance | Better robustness for missing-eye-protection inference |
| `boots` | YOLOv8n | Same runtime stack as existing PPE models | Fast integration with existing overlays/alerts |
| `faceshield` | YOLOv8n | Works with existing class-filter inference path | Consistent deployment and maintenance path |
| `safetysuit` | YOLOv8n | Keeps PPE logic unified across garment classes | Low-friction extension to per-camera policy controls |
| `fatigue` | SwinV2-S + dlib landmarks + OpenCV PnP | Fatigue is behavior/state, not only object presence | Hybrid explainable scoring with tunable safety thresholds |

---

## 3. Backend Architecture

### 3.1 Django Configuration

| Setting | Value |
|---------|-------|
| **Framework** | Django 5.x |
| **ASGI Server** | Daphne |
| **Database** | SQLite (`backend/monitoring.db`) |
| **Channel Layer** | InMemoryChannelLayer |
| **REST Framework** | Django REST Framework with LimitOffsetPagination (100 per page) |
| **CORS** | All origins allowed (development mode) |

**Installed Apps:**
`daphne`, `rest_framework`, `corsheaders`, `channels`, `cameras`, `detection`, `alerts`, `devlab`

**Middleware Stack:**
CorsMiddleware → SecurityMiddleware → SessionMiddleware → CommonMiddleware → AuthenticationMiddleware → MessagesMiddleware

### 3.2 ASGI & WebSocket Routing

The application uses Django Channels' `ProtocolTypeRouter` to handle both HTTP and WebSocket connections on a single port:

```
ProtocolTypeRouter
├── "http"      → Django ASGI application (all REST endpoints)
└── "websocket" → URLRouter
  ├── ws/alerts/                     → AlertConsumer
  ├── ws/cameras/{camera_id}/stream/ → CameraStreamConsumer
  └── ws/video-analysis/             → VideoAnalysisConsumer
```

### 3.3 Database Schema

#### Camera

| Field | Type | Description |
|-------|------|-------------|
| id | AutoField (PK) | Primary key |
| name | CharField(255) | Camera display name |
| source_url | CharField(500) | RTSP URL or device index |
| location | CharField(255) | Physical location (optional) |
| is_active | BooleanField | Enabled/disabled flag |
| created_at | DateTimeField | Auto-set on creation |

#### ModelSetting

| Field | Type | Description |
|-------|------|-------------|
| key | CharField (PK) | Model identifier (`helmet`, `fatigue`, `vest`, `gloves`, `goggles`, `boots`, `faceshield`, `safetysuit`) |
| is_enabled | BooleanField | Global enable/disable toggle |

#### CameraModel (Per-Camera Override)

| Field | Type | Description |
|-------|------|-------------|
| id | AutoField (PK) | Primary key |
| camera | ForeignKey → Camera | Associated camera |
| model_setting | ForeignKey → ModelSetting | Associated model |
| is_enabled | BooleanField | Override enable state |

Unique constraint: `(camera, model_setting)` — one override per camera-model pair.

#### Detection

| Field | Type | Description |
|-------|------|-------------|
| id | AutoField (PK) | Primary key |
| camera | ForeignKey → Camera | Source camera |
| model_key | CharField(50) | Model that produced this detection |
| payload | JSONField | Full inference result |
| confidence | FloatField | Detection confidence score |
| status | CharField | ok, error, unavailable |
| detected | BooleanField | Whether the condition was detected |
| created_at | DateTimeField | Indexed, descending |

#### Alert

| Field | Type | Description |
|-------|------|-------------|
| id | AutoField (PK) | Primary key |
| detection | ForeignKey → Detection | Triggering detection (nullable) |
| camera | ForeignKey → Camera | Source camera |
| model_key | CharField(50) | Model that triggered the alert |
| severity | CharField | high, medium, low |
| status | CharField | open, acknowledged |
| message | TextField | Human-readable alert description |
| payload | JSONField | Additional context data |
| created_at | DateTimeField | Indexed, descending |
| acknowledged_at | DateTimeField | Timestamp of acknowledgment (nullable) |

#### CameraAlertSeverity

| Field | Type | Description |
|-------|------|-------------|
| id | AutoField (PK) | Primary key |
| camera | ForeignKey → Camera | Target camera |
| model_key | CharField(50) | Model severity is defined for |
| severity | CharField | high, medium, low |
| updated_at | DateTimeField | Last policy update timestamp |

Unique constraint: `(camera, model_key)`.

**Severity Resolution:** `CameraAlertSeverity` override (if present) → default map in `alerts/services.py`.

#### DevVideo

| Field | Type | Description |
|-------|------|-------------|
| id | AutoField (PK) | Primary key |
| original_filename | CharField(255) | Original upload name |
| file_path | CharField(500) | Local storage path |
| file_size | BigIntegerField | File size in bytes |
| duration | FloatField | Video duration in seconds (nullable) |
| uploaded_at | DateTimeField | Auto-set on creation |

### 3.4 Django Applications

#### Cameras App

Handles camera CRUD, connectivity checks, MJPEG streaming, and device discovery.

**Key Features:**
- **MJPEG Streaming:** `StreamingHttpResponse` with multipart/x-mixed-replace content type, yielding JPEG-encoded frames
- **Annotated Streams:** Optional real-time annotation overlay — live camera stream inference runs periodically (5-frame cadence) with cached intermediate overlays
- **Device Discovery:** Probes system camera indices 0–9, returns available devices with resolution info
- **Background Model Loading:** Models preload asynchronously so raw frames start streaming immediately

#### Detection App

Manages model settings, per-camera overrides, and the inference adapter.

**Inference Adapter (`_DjangoInferenceAdapter`):**
- Singleton pattern via `get_inference_service()`
- Lazy model initialization with thread-safe double-check locking
- `preload()` for background model warming
- `run_inference(model_key, source_url, camera_id)` — captures frame and runs inference
- `run_inference_on_frame(model_key, frame, camera_id)` — runs inference on a provided frame

#### Alerts App

Manages alert records and WebSocket broadcasting.

**AlertConsumer (WebSocket):**
- On connect: joins the `alerts` channel group
- On disconnect: leaves the group
- Broadcasts two message types:
  - `alert.new` — when a new alert is created
  - `alert.acknowledged` — when an alert is acknowledged

**Alert Creation Flow:**
1. Detection model reports a finding with confidence ≥ threshold
2. `create_alert()` creates a database record
3. `broadcast_alert()` sends the alert to the `alerts` WebSocket group
4. All connected clients receive the alert in real-time

**Severity Policy Features:**
- Per-camera, per-model severity is editable through API/UI.
- A one-time "apply global override" action writes selected severities to all camera policies.
- The global apply action does not lock camera policies; camera values remain editable afterward.

#### DevLab App

Provides developer tools: video upload/analysis, threshold tuning, and system performance monitoring.

**VideoAnalysisConsumer (WebSocket):**
- Receives `start` action with `video_id` and `sample_every_n_frames`
- Spawns a background daemon thread for non-blocking processing
- Sends frame-by-frame detection results as they complete
- Message protocol: `init` → `frame` (repeated) → `done`
- Supports `stop` action for cancellation via `threading.Event`

**Performance Endpoint:**
- Returns CPU %, RAM (MB), GPU %, GPU VRAM (used/total)
- GPU stats via `nvidia-smi` subprocess with `torch.cuda` fallback

### 3.5 REST API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health/` | Health check |
| GET/POST | `/api/v1/cameras/` | List or create cameras |
| GET/PUT/DELETE | `/api/v1/cameras/{id}/` | Camera CRUD |
| GET | `/api/v1/cameras/discover/` | Discover local video devices |
| POST | `/api/v1/cameras/probe/` | Validate a source URL and return JPEG preview frame |
| GET | `/api/v1/cameras/{id}/status/` | Camera connectivity check |
| GET | `/api/v1/cameras/{id}/snapshot/` | Single frame snapshot |
| GET | `/api/v1/cameras/{id}/stream/` | MJPEG stream (`?annotated=1&overlays=helmet,fatigue`) |
| GET | `/api/v1/models/` | List model settings |
| GET/PUT | `/api/v1/models/{key}/` | Single model setting |
| GET | `/api/v1/cameras/models/overrides/` | Bulk camera-model override state |
| GET | `/api/v1/cameras/{id}/models/` | Per-camera model overrides |
| PUT | `/api/v1/cameras/{id}/models/{key}/` | Single camera-model override |
| POST | `/api/v1/detections/analyze/` | Run inference on camera frame |
| GET | `/api/v1/detections/` | List detection records |
| GET | `/api/v1/alerts/` | List alerts (filterable by status, severity, camera) |
| PATCH | `/api/v1/alerts/{id}/acknowledge/` | Acknowledge an alert |
| GET | `/api/v1/alerts/severity/matrix/` | Get effective severity matrix (models × cameras) |
| PUT | `/api/v1/alerts/severity/cameras/{camera_id}/{model_key}/` | Set severity for one camera-model pair |
| POST | `/api/v1/alerts/severity/apply-global/` | One-time apply severity map to all cameras |
| GET/POST | `/api/v1/dev/videos/` | List or upload videos |
| GET | `/api/v1/dev/videos/{id}/file/` | Download video file |
| GET | `/api/v1/dev/videos/{id}/stream/` | MJPEG video stream |
| POST | `/api/v1/dev/videos/{id}/analyze/` | Batch video analysis |
| GET/PUT | `/api/v1/dev/thresholds/` | Get/set detection thresholds |
| GET | `/api/v1/dev/performance/` | System resource metrics |

**WebSocket Endpoints:**

| URL | Consumer | Purpose |
|-----|----------|---------|
| `ws://host/ws/alerts/` | AlertConsumer | Real-time alert push |
| `ws://host/ws/cameras/{camera_id}/stream/` | CameraStreamConsumer | Binary JPEG camera streaming with dynamic overlays |
| `ws://host/ws/video-analysis/` | VideoAnalysisConsumer | Live video analysis streaming |

### 3.6 API Usage Matrix

This project uses both **internal application APIs** and **external service interfaces**.

| API / Interface | Type | Used For | Why this choice |
|-----------------|------|----------|-----------------|
| DRF REST (`/api/v1/*`) | Internal HTTP API | CRUD, settings, analytics, exports, thresholds | Easy schema evolution, predictable integration for React views |
| Channels WebSocket (`/ws/*`) | Internal realtime API | Push alerts, low-latency streams, video-analysis frames | Lower polling overhead and better UX for live operations |
| Ultralytics Python API (`YOLO(...)`) | External library API | Load/infer YOLO checkpoints; expose class metadata | Fast integration and consistent inference code path |
| PyTorch API | External library API | Load/run Swin checkpoint and tensor transforms | Required runtime for transformer fatigue model |
| dlib API | External library API | 68-point landmarks for EAR/MAR/pose inputs | Stable classical face landmarks; interpretable signals |
| OpenCV API | External library API | Capture, encode, draw overlays, PnP head pose, QR detection | Production-ready CV primitives with strong ecosystem support |
| MediaPipe API | External library API | Hand/face feature regions to assist glove/goggle absence logic | Improves robustness where object classes are small/ambiguous |
| HuggingFace model URLs (HTTP) | External model source | Optional automatic model downloads on missing files | Simplifies first-run setup and model distribution |
| `nvidia-smi` CLI query | External system API | GPU utilization/memory telemetry for DevLab | Lightweight and vendor-standard metrics path |

---

## 4. Frontend Architecture

### 4.1 Application Structure

The frontend is a React 18 SPA built with Vite and styled with Tailwind CSS v4, using a dark "Tactical HUD" theme.

**Dependencies:**

| Package | Version | Purpose |
|---------|---------|---------|
| react | 18.3.1 | UI framework |
| react-dom | 18.3.1 | DOM rendering |
| react-router-dom | 7.13.1 | Client-side routing |
| vite | 5.4.10 | Build tool and dev server |
| tailwindcss | 4.2.1 | Utility-first CSS |

**Routing:**

| Path | Component | Description |
|------|-----------|-------------|
| `/` | LandingPage | Project overview and launch CTA |
| `/feeds` | FeedsPage | Live camera grid with alert sidebar |
| `/alerts` | AlertsPage | Alert center with grouping modes |
| `/models` | ModelsPage | Model + severity policy management |
| `/devlab` | DevLabPage | Video analysis, live camera test, threshold tuning |

**Build Configuration (vite.config.js):**
- Dev server proxies `/api` → `http://localhost:7860` and `/ws` → `ws://localhost:7860`
- Production: Django serves the built `frontend/dist/` directory

### 4.2 Pages

#### Live Camera Feeds (`/feeds`)

- **Camera Grid:** 2-column layout with a hero camera (promoted on click)
- **MJPEG/WebSocket Streams:** Camera tiles consume live stream frames from backend camera stream endpoints
- **Add Camera Dialog:** Form with device discovery integration — scans local camera indices
- **Alert Sidebar:** 280px right panel showing the latest open alerts grouped by severity
- **Polling:** Alerts refresh every 5 seconds via REST
- **Hugging Face Demo Guardrail:** Full-page warning in the main area (dismissible) because camera access is not supported on HF-hosted demo URLs; a smaller warning persists after dismissal
- **Badge De-duplication:** Camera badges are grouped by alert type and display elapsed time since last trigger

#### Alert Center (`/alerts`)

- **Grouping Modes:** Severity, Camera, Model, Time — buttons in the header toggle the mode
- **Alert List:** Color-coded severity bars (red/amber/blue), message, camera name, timestamp
- **Detail Panel:** 320px fixed right panel showing full alert metadata and JSON payload
- **Acknowledge Workflow:** Click acknowledge button → PATCH API → status updates to "acknowledged"
- **Polling:** Full alert list refreshes every 5 seconds

#### Model Management (`/models`)

- **Global Model Settings:** Grid of model cards with toggle switches
- **Per-Camera Overrides:** Table with cameras as rows, models as columns, toggle switches in each cell
- **Override Resolution:** Per-camera setting overrides global; if no override exists, global setting applies
- **Alert Severity Settings:**
  - Per-camera, per-model severity (`high|medium|low`) is editable directly in matrix form
  - Global one-time override applies selected severities to all cameras
  - Global apply does not lock per-camera editing

#### Developer Lab (`/devlab`)

Three tabs (all stay mounted to preserve state):

**Tab 1 — Video Analysis:**
- Drag-and-drop video upload
- WebSocket-based live analysis: video plays while analysis runs concurrently
- `<video>` + `<canvas>` overlay pattern for real-time annotation drawing
- Buffer-gated synchronization: video pauses when it catches up to analysis, resumes when 1s buffer ahead
- Binary search (`findNearest`) maps current playback time to nearest analyzed frame
- Execution log with timestamped entries

**Tab 2 — Live Camera Test:**
- Camera selection buttons
- MJPEG stream with configurable overlay toggles

**Tab 3 — Threshold Tuning:**
- Sliders for confidence, EAR threshold, MAR threshold, head tilt degrees, consecutive frames
- Changes apply immediately via REST PUT

**Floating Performance Monitor:**
- Bottom-right widget showing CPU, RAM, GPU, VRAM
- Polled every 3 seconds
- Color-coded health indicators (green/amber)

### 4.3 Shared Components

| Component | Purpose |
|-----------|---------|
| **IconRail** | Vertical navigation sidebar (56px) with route links and alert count badge |
| **CameraFeed** | Live camera stream tile with name/location overlay, LIVE indicator, delete button |
| **AlertCard** | Compact alert display with severity color, message, camera, time |
| **Badge** | Colored status badge (danger, warning, success, info, muted) |
| **Toggle** | Animated on/off switch (sm/md sizes) |
| **Toast** | Bottom-right notification stack, manual dismiss + auto-dismiss (~8s) |
| **LoadingCircle** | Centered spinner used for route and page-level loading states |

### 4.4 State Management

The application uses **component-level state** exclusively — no Redux, Zustand, or Context API. Each page manages its own state via `useState` and `useEffect`.

| Scope | State | Location |
|-------|-------|----------|
| Global | Alert count, toast notifications, route-transition loading | DashboardLayout.jsx |
| Feeds | Cameras, alerts, heroId, HF warning dismissal, badge timers | FeedsPage.jsx |
| Alerts | Alert list, groupBy mode, selected alert | AlertsPage.jsx |
| Models | Model settings, camera overrides, severity matrix, one-time global severity draft | ModelsPage.jsx |
| DevLab | Video file/metadata, analysis state, logs, thresholds | DevLabPage.jsx |

**Performance-Critical State (DevLab Video Analysis):**
Uses React refs to bypass batched state updates in the annotation draw loop:
- `frameMapRef` — Map of frame number → detections (O(1) lookup)
- `sortedFramesRef` — Sorted frame array for binary search
- `fpsRef`, `runningRef`, `analysisDoneRef` — flags read in `requestAnimationFrame` loop
- `playbarRef` — direct DOM manipulation for progress bar (avoids re-renders)

### 4.5 WebSocket Client

**Alert Socket (`ws.js`):**
- Factory function `createAlertSocket(onMessage)` creates a WebSocket connection
- Auto-reconnects every 3 seconds on disconnect
- Detects secure/insecure protocol from `window.location`
- Returns `{ close() }` handle for cleanup

**Video Analysis Socket (inline in DevLabPage):**
- Created on-demand when user starts analysis
- Sends `start`/`stop` actions
- Receives `init`, `frame`, `done`, `error` messages
- Frames stored in `frameMapRef` for O(1) draw-loop access

### 4.6 Design System

**Theme:**
- Background: `#09090b` with subtle blue-tinted grid pattern
- Surface: `#18181b` (cards), `#111113` (nested panels)
- Accent: Blue (#3b82f6)
- Fonts: DM Sans (headings/body), JetBrains Mono (code/metrics)

**Animations:**
- `pulse-dot` (2s) — live indicator
- `scan` (4s) — horizontal scan line on hero camera
- `slide-in` (0.3s) — toast notification entry
- `animate-spin` — loading indicators and in-progress controls

---

## 5. Real-Time Data Flow

### Alert Pipeline

```
Camera Frame
    │
    ▼
Inference Service (runs enabled models)
    │
    ▼
Detection record saved to DB
    │
    ├── confidence < threshold → no alert
    │
    └── confidence ≥ threshold
        │
        ▼
    Severity resolved:
      camera-model override (if set) else default map
      │
      ▼
    Alert record created
        │
        ▼
    broadcast_alert() → Channels group_send("alerts", ...)
        │
        ▼
    AlertConsumer.alert_new() → WebSocket push to all clients
        │
        ▼
    DashboardLayout onMessage → increment alertCount, show Toast
```

### Video Analysis Pipeline

```
User uploads video → POST /api/v1/dev/videos/
    │
    ▼
User clicks "Play & Analyze Live"
    │
    ├── Frontend: ws.send({action: "start", video_id, sample_every_n_frames})
    │
    └── Frontend: video.play() (buffer-gated)
        │
        ▼
Server: VideoAnalysisConsumer._run() (background thread)
    │
    ├── ws.send({type: "init", fps, total_frames, enabled_models})
    │
    ├── For each sampled frame:
    │   ├── Run all enabled models
    │   └── ws.send({type: "frame", frame: N, detections: {...}})
    │
    └── ws.send({type: "done"})
        │
        ▼
Frontend: frameMapRef.set(N, detections)
    │
    ▼
requestAnimationFrame draw loop:
    ├── Get video.currentTime → compute current frame
    ├── Binary search sortedFramesRef for nearest analyzed frame
    ├── Look up detections in frameMapRef
    ├── Draw PPE boxes and fatigue annotations on <canvas>
    └── Sync: pause if buffer < 0.15s, resume if buffer ≥ 1.0s
```

---

## 6. Configuration & Thresholds

All thresholds are defined in `backend/config.py` and tunable via the Dev Lab:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DEFAULT_ALERT_CONFIDENCE_THRESHOLD` | 0.45 | Minimum confidence to trigger an alert |
| `FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD` | 8 | Consecutive fatigued frames before alert |
| `HEAD_TILT_ALERT_DEGREES` | 15.0 | Maximum head tilt before alert |
| `EAR_THRESHOLD` | 0.21 | Eye Aspect Ratio threshold (Dev Lab) |
| `MAR_THRESHOLD` | 0.65 | Mouth Aspect Ratio threshold (Dev Lab) |
| YOLO inference confidence | 0.35 | Minimum confidence for YOLO detections |
| Fatigue hybrid threshold | 0.55 | `hybrid_score ≥ 0.55` triggers `is_fatigued` |
| Hybrid weights | 60/30/10 | ML probability / EAR score / MAR score |
| Annotation frame skip | 3 | Run inference every Nth frame in streams |

**Model Weight Paths (auto-downloaded from HuggingFace):**

| Model | File | Source |
|-------|------|--------|
| Helmet | `ml_models/best.pt` | keremberke/yolov8n-hard-hat-detection |
| Vest | `ml_models/vest_detection.pt` | Project-local / optional PPE source |
| Gloves | `ml_models/gloves_detection.pt` | Project-local |
| Goggles | `ml_models/goggles_detection.pt` | Project-local |
| Boots | `ml_models/boots_detection.pt` | keremberke/yolov8n-boots-detection (configured URL) |
| Face Shield | `ml_models/faceshield_detection.pt` | Project-local |
| Safety Suit | `ml_models/safety_suit_detection.pt` | Project-local |
| Person | `ml_models/yolov8n.pt` | ultralytics/assets |
| Swin Fatigue | `ml_models/swin_best.pth` | Custom trained |
| Shape Predictor | `ml_models/shape_predictor_68_face_landmarks.dat` | dlib-models |

---

## 7. Deployment

### Development

```bash
python run.py  # Starts both servers
# Backend: Daphne on port 7860
# Frontend: Vite on port 5173 (proxies /api and /ws to 7860)
```

### Production

```bash
cd frontend && npm run build    # Build React app to dist/
cd backend && daphne -b 0.0.0.0 -p 7860 sentinel.asgi:application
```

Django serves the built frontend from `frontend/dist/`. No separate frontend server needed.

### Docker

```bash
docker build -t sentinel .
docker run -p 7860:7860 sentinel
```

The Dockerfile uses Miniconda for dlib compatibility, installs all Python and Node dependencies, builds the frontend, and runs Daphne.

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python** | 3.10+ | 3.10 |
| **Node.js** | 18+ | 20 LTS |
| **RAM** | 4 GB | 8 GB |
| **GPU** | None (CPU inference) | NVIDIA with CUDA (10x faster) |
| **GPU VRAM** | — | 4 GB+ |
| **Disk** | 2 GB (models) | 4 GB |
