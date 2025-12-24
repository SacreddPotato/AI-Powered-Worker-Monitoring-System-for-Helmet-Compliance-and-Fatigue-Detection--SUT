# Backend - Flask Application

This directory contains the Flask backend for the AI Worker Monitoring System.

## Features
- Real-time video processing for helmet and fatigue detection
- YOLOv8 helmet detection
- Hybrid fatigue detection (Swin Transformer + Geometric Analysis)
- Video upload and webcam support

## Setup

### Prerequisites
- Python 3.8+
- Webcam (for real-time detection)

### Installation

1. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies using conda** (recommended)
   ```bash
   conda env create -f environment.yml
   conda activate fatigue-detection
   ```

   Or **using pip**:
   ```bash
   pip install flask opencv-python ultralytics dlib torch torchvision numpy scipy
   ```

### Required Model Files

The following files should be present in this directory:
- `AIHelmet/best.pt` - YOLOv8 helmet detection model
- `shape_predictor_68_face_landmarks.dat` - Dlib face landmarks model
- `swin_best.pth` - Swin Transformer fatigue detection model

## Running the Application

### Production Mode (Recommended)
```bash
python app.py
```

The server will start on `http://localhost:5000` with debug mode disabled by default.

### Development Mode (with auto-reload)
```bash
export FLASK_DEBUG=true  # On Windows: set FLASK_DEBUG=true
python app.py
```

**⚠️ Security Note:** Never run with debug mode enabled in production environments.

## API Endpoints

### Page Routes
- `/` - Main page
- `/fatigue.html` - Fatigue detection interface
- `/helmet.html` - Helmet detection interface

### Video Streaming
- `/video_feed` - Fatigue detection video stream
  - Query param: `source` (default: '0' for webcam)
- `/helmet_video_feed` - Helmet detection video stream
  - Query param: `source` (default: '0' for webcam)

### Upload Endpoints
- `POST /upload_video` - Upload video for fatigue detection
- `POST /upload_helmet_video` - Upload video for helmet detection

## Directory Structure

```
backend/
├── app.py                  # Flask application
├── camera.py               # Video processing logic
├── AIHelmet/              # Helmet detection model
│   └── best.pt
├── templates/             # Flask HTML templates
│   └── index.html
├── uploads/               # User-uploaded videos
├── shape_predictor_68_face_landmarks.dat
├── swin_best.pth
└── environment.yml        # Conda environment file
```

## Notes

- The Flask app serves its own templates from the `templates/` folder
- For the static GitHub Pages website, see the `docs/` folder in the root directory
- Uploaded videos are stored in `uploads/` directory
- Use webcam by default (source='0') or provide video file path/URL
