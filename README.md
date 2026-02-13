---
title: AI Worker Safety Monitor
emoji: 👷
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AI-Powered Worker Monitoring System
### Helmet Compliance & Fatigue Detection for Industrial Safety

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-lightgrey?style=for-the-badge&logo=flask)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-orange?style=for-the-badge&logo=pytorch)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green?style=for-the-badge&logo=opencv)
![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

## 🎓 Project Abstract

This repository contains the implementation and documentation for the **Senior Capstone Project** conducted at **El Sewedy University of Technology (SUT)**. 

The primary objective of this research is to address safety challenges in industrial environments by automating the monitoring of worker protocols. By leveraging **Computer Vision** and **Deep Learning** techniques, the proposed system provides a non-intrusive, real-time solution for:
1.  **PPE Compliance Verification:** Ensuring adherence to safety helmet regulations.
2.  **Operator Fatigue Analysis:** Detecting physiological signs of drowsiness to prevent accidents.

The system integrates state-of-the-art models, including **YOLOv8** for object detection and **Swin Transformers** for facial analysis, encapsulated within a **Flask** web architecture.

---

## 👥 Project Team

**Full Stack Implementation:**
* Shaza Alaa
* Battol Mohamed

**Model Development & Optimization:**
* Ahmed Baher
* Omar Diab
* Omar Saad
* Haneen Ahmed

---

## 🔬 Methodology & System Modules

### 1. Automated Helmet Compliance
**Algorithm:** YOLOv8 (Custom & Pre-trained)

To verify Personal Protective Equipment (PPE) compliance, the system utilizes a dual-inference approach:
* **Person Detection:** A standard `yolov8n` model identifies individuals within the frame.
* **Helmet Detection:** A custom-trained YOLOv8 model (`best.pt`) identifies safety helmets.
* **Correlation Logic:** The system computes the spatial intersection and proximity between detected persons and helmets. A non-compliance alert is triggered specifically when a "Person" bounding box lacks a corresponding overlapping "Helmet" bounding box in the cranial region.

### 2. Fatigue Detection V1: Hybrid Approach
**Algorithm:** Geometric Analysis (Dlib) + Visual Transformers (Swin-V2)

This module implements a robust, multi-modal fusion strategy to ensure detection accuracy across varying lighting conditions and occlusions (e.g., eyewear):
* **Geometric Stream:** Utilizes `dlib` 68-point facial landmarks to calculate:
    * **Eye Aspect Ratio (EAR):** To quantify eye closure duration.
    * **Mouth Aspect Ratio (MAR):** To identify yawning events.
    * **Head Pose Estimation:** To track pitch, yaw, and roll for signs of nodding.
* **Visual Stream:** A **Swin Transformer V2** processes the raw facial image to extract high-level fatigue features.
* **Decision Fusion:** The final fatigue score is derived via a weighted equation:
    $$Score = (P_{model} \times 0.6) + (S_{droop} \times 0.3) + (S_{MAR} \times 0.1)$$.

  
    *Where P is probability and S is the calculated geometric score.*

### 3. Fatigue Detection V2: State Classification
**Algorithm:** Convolutional Neural Network (CNN)

An alternative deep learning model designed for granular state classification. This custom CNN processes 112x112 aligned face images to categorize the subject into three distinct alertness states:
1.  **Alert:** Subject is fully attentive.
2.  **Non-Vigilant:** Subject exhibits early signs of drowsiness.
3.  **Tired:** Subject exhibits active fatigue or yawning.

---

## 🛠️ Technical Architecture

### Repository Structure

    .
    ├── backend/
    │   ├── app.py                  # Application Gateway (Flask)
    │   ├── camera.py               # Implementation of Hybrid Fatigue Logic
    │   ├── helmet_camera.py        # Implementation of YOLO Helmet Logic
    │   ├── fatigue_v2_api.py       # Inference Engine for CNN Model
    │   ├── environment.yml         # Conda Environment Specification
    │   ├── best.pt                 # Trained Helmet Detector
    │   ├── swin_best.pth           # Trained Swin Transformer
    │   └── best_fatigue_model2.pth # Trained 3-Class CNN
    ├── docs/                       # Client-Side Interface (HTML/CSS/JS)
    │   ├── assets/                 # Static Resources
    │   └── *.html                  # Interface Templates
    ├── Dockerfile                  # Containerization Config
    └── requirements.txt            # Python Dependencies

### Frameworks & Libraries
* **Core Runtime:** Python 3.10
* **Web Architecture:** Flask
* **Computer Vision:** OpenCV, Dlib, Pillow
* **Machine Learning:** PyTorch, Ultralytics YOLO
* **Deployment:** Docker, Git LFS

---

## 💻 Setup & Installation

### Prerequisites
* **Git** (Git LFS required for large model files).
* **Docker Engine** (Recommended) OR **Python 3.10** with Conda.

### Option A: Docker Deployment (Recommended)
Docker is recommended to automate the compilation of `dlib` dependencies.

1.  **Clone Repository:**
    ```bash
    git clone [https://github.com/SacreddPotato/worker-monitoring-system.git](https://github.com/SacreddPotato/worker-monitoring-system.git)
    cd worker-monitoring-system
    ```

2.  **Build Image:**
    ```bash
    docker build -t worker-monitor .
    ```

3.  **Launch Container:**
    ```bash
    docker run -p 7860:7860 worker-monitor
    ```
    The interface will be accessible at `http://localhost:7860`.

### Option B: Local Environment (Conda)
If running locally, Conda is advised for managing binary dependencies.

1.  **Initialize Environment:**
    ```bash
    conda env create -f backend/environment.yml
    conda activate fatigue_env
    ```

2.  **Model Acquisition:**
    Ensure Git LFS has pulled the actual `.pt` and `.pth` files in `backend/` (not pointer files).

3.  **Execution:**
    ```bash
    python backend/app.py
    ```

---

## 📊 Data Sources

The models utilized in this study were trained and validated using the following open-access datasets:

* **Helmet Detection:** [Kaggle Hard Hat Detection Dataset](https://www.kaggle.com/datasets/andrewmvd/hard-hat-detection).
* **Fatigue Analysis:** [UTA-RLDD Fatigue Detection Dataset](https://www.kaggle.com/datasets/minhngt02/uta-rldd) (Binary & Multi-class variations).

---

## 🔒 Ethical Considerations

* **Privacy by Design:** The system architecture processes video streams in volatile memory (RAM). No video data is persisted to disk or external databases during standard operation, ensuring the privacy of monitored individuals.
* **Data Retention:** The "Upload" feature for testing purposes stores files temporarily in `backend/uploads`, which are subject to ephemeral storage policies.

---

## 📄 License
This project is released under the **Unlicense License**.
