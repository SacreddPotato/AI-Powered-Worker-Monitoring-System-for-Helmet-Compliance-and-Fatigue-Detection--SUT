---
title: AI Worker Safety Monitor
emoji: 👷
colorFrom: yellow
colorTo: orange
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AI-Powered Worker Monitoring System

A computer vision system for **Helmet Compliance** and **Fatigue Detection** designed to enhance workplace safety.

🎓 **Senior Capstone Project** | Team of 6 Students @ El Sewedy University of Technology (SUT)

---

## 🌐 Live Demo

**[View Project Dashboard (Frontend only)](https://sacreddpotato.github.io/AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT/)**

**[View Project Dashboard (Model Functionality included - Might be slightly altered or behind in some changes)](https://huggingface.co/spaces/SacreddPotato/worker-monitoring-system)**

The frontend interface is hosted via GitHub Pages in the `docs/` folder.

The Functional dashboard is hosted via huggingfaces.

---

## 🚀 Features

### 1. **AI Helmet Detection**
- **Model:** YOLOv8 (Custom Trained)
- **Function:** Real-time bounding box detection for Personal Protective Equipment (PPE).
- **Performance:** Optimized for varying lighting conditions and head angles.

### 2.1. **Fatigue Detection (Hybrid Approach)**
- **Geometric Analysis:** Tracks 68 facial landmarks (Dlib) to calculate Eye Aspect Ratio (EAR) and Mouth Aspect Ratio (MAR).
- **Deep Learning:** Uses a **Swin Transformer** backbone to analyze visual fatigue features.
- **Logic:** Weighted average of geometric and visual scores triggers alerts when fatigue > 0.50.

### 2.2. **Fatigue Detection (Alternative Model)**
- **Multiple Classes:** Person is classified into three states, Alert, Non-vigilant and fatigued.

---

## 📂 Project Structure

This project is structured to run as a Docker container:
* `Dockerfile`: Defines the environment and installation steps.
* `backend/`: Contains the Flask application (`app.py`) and AI inference logic.
* `docs/`: Static assets and frontend templates.
* `requirements.txt`: Python dependencies.
