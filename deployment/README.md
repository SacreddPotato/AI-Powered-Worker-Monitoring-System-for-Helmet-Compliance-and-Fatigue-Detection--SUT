---
title: AI Worker Safety Monitor
emoji: 👷
colorFrom: yellow
colorTo: orange
sdk: docker
pinned: false
license: mit
---

# 👷 AI-Powered Worker Monitoring System
### Helmet Compliance & Fatigue Detection

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces) 
[![Python](https://img.shields.io/badge/Python-3.9-3776AB)](https://www.python.org/) 
[![Flask](https://img.shields.io/badge/Flask-Web%20App-000000)](https://flask.palletsprojects.com/)

An AI-powered computer vision system designed to enhance workplace safety. This full-stack application detects whether workers are wearing safety helmets and monitors facial landmarks to detect signs of fatigue (drowsiness) in real-time.

---

## 🚀 Live Demo

**[Insert your Hugging Face Space Link Here]** *Note: The application is hosted on Hugging Face Spaces using Docker.*

---

## 🌟 Key Features

### 1. ⛑️ Helmet Detection
- **Model:** YOLOv8 (Fine-tuned)
- **Function:** Real-time object detection to verify if a safety helmet is present on the worker's head.
- **Status:** Integrated & Deployed.

### 2. 😴 Fatigue Detection
- **Model:** Dlib 68-Point Face Landmark Predictor & Swin Transformer
- **Function:** Monitors Eye Aspect Ratio (EAR) and other facial cues to detect drowsiness or distraction.
- **Alerts:** Visual alerts when fatigue thresholds are breached.

### 3. 📹 Flexible Input Support
- **Webcam:** Live streaming from the user's camera.
- **Video Upload:** Upload pre-recorded video files (`.mp4`, `.avi`, etc.) for analysis.

---

## 🛠️ Tech Stack

* **Backend:** Flask (Python)
* **Computer Vision:** OpenCV, Dlib, Ultralytics YOLO
* **Deep Learning:** PyTorch, Swin Transformer
* **Deployment:** Docker, Hugging Face Spaces

---

## 💻 Local Installation

If you want to run this application locally instead of on the cloud:

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Install System Dependencies (Linux/Mac)**
    * *Windows users usually need to install CMake and Visual Studio Build Tools first.*
    ```bash
    sudo apt-get install cmake build-essential libgl1-mesa-glx
    ```

3.  **Install Python Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    ```bash
    python app.py
    ```
    The app will start at `http://localhost:7860`.

---

## ☁️ Deployment Guide (Hugging Face)

This project is configured for deployment on **Hugging Face Spaces** using the Docker SDK.

1.  Create a new Space on [Hugging Face](https://huggingface.co/new-space).
2.  Select **Docker** as the SDK.
3.  Upload the contents of this branch (ensure `Dockerfile` is in the root).
4.  **Important:** Ensure the large model files are included via Git LFS or direct upload:
    * `AIHelmet/best.pt`
    * `swin_best.pth`
    * `shape_predictor_68_face_landmarks.dat`

### Docker Configuration
The `Dockerfile` handles the complex installation of `dlib` and `opencv-python-headless`:
* Base Image: `python:3.9-slim`
* Port: `7860`
* Permissions: Sets up a writable `uploads/` directory for video processing.

---

## 📁 Project Structure
