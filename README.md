# AI-Powered Worker Monitoring System

A computer vision system for **Helmet Compliance** and **Fatigue Detection** designed to enhance workplace safety.

🎓 **Senior Capstone Project** | Team of 6 Students @ El Sewedy University of Technology (SUT)

---

## 🌐 Live Demo

**[View Project Dashboard (Frontend only)](https://sacreddpotato.github.io/AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT/)**
**[View Project Dashboard (Model Functionality included - Might be slightly altered or behind in some changes)](https://sacreddpotato.github.io/AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT/)**

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

## 📁 Project Structure

```text
/
├── docs/                    # Static Frontend (HTML/JS/CSS)
│   ├── index.html          # Dashboard Home
│   ├── helmet.html         # Helmet Demo Interface
│   ├── fatigue.html        # Fatigue Demo Interface
│   └── assets/             # Project Assets
│
├── backend/                 # Flask API & Inference Engine
│   ├── app.py              # Main Application Server
│   ├── camera.py           # Video Stream Processing
│   ├── AIHelmet/           # YOLOv8 Model Weights
│   ├── swin_best.pth       # Swin Transformer Weights
│   └── shape_predictor...  # Dlib Landmark Predictor
│
└── README.md               # Documentation
