# AI-Powered Worker Monitoring System

AI-powered system for **Helmet Compliance Detection** and **Fatigue Detection** to enhance workplace safety.

🎓 **Student Project** | El Sewedy University of Technology (SUT)

---

## 🌐 Live Website

Visit the project website: [GitHub Pages](https://sacreddpotato.github.io/AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT/)

The static website is located in the `docs/` folder and deployed via GitHub Pages.

---

## 📁 Project Structure

```
/
├── docs/                    # Static website (GitHub Pages)
│   ├── index.html          # Homepage
│   ├── about.html          # About the project
│   ├── helmet.html         # Helmet detection info
│   ├── fatigue.html        # Fatigue detection info
│   ├── faq.html            # FAQ page
│   ├── contact.html        # Contact page
│   ├── demo.html           # Demo request page
│   ├── styles.css          # Main stylesheet
│   ├── app.js              # Frontend JavaScript
│   └── assets/             # Images and media files
│
├── backend/                 # Flask application & AI models
│   ├── app.py              # Flask web server
│   ├── camera.py           # Video processing logic
│   ├── AIHelmet/           # Helmet detection model
│   │   └── best.pt         # YOLOv8 trained model
│   ├── shape_predictor_68_face_landmarks.dat  # Dlib landmarks
│   ├── swin_best.pth       # Swin Transformer model
│   ├── templates/          # Flask templates
│   ├── uploads/            # Uploaded videos
│   └── environment.yml     # Conda environment
│
├── README.md               # This file
└── tests.py                # Test file
```

---

## 🚀 Features

### 1. **AI Helmet Detection**
- Real-time helmet compliance detection using YOLOv8
- Detects whether workers are wearing safety helmets
- Custom-trained model for high accuracy

### 2. **Fatigue Detection**
- Hybrid approach combining Swin Transformer and geometric analysis
- Eye Aspect Ratio (EAR) monitoring
- Head pose estimation
- Yawn detection
- Real-time alerting system

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Conda (recommended) or pip
- Webcam (for real-time detection)
- **Required Model Files** (see `backend/MODELS.md` for download instructions)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SacreddPotato/AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT.git
   cd AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT
   ```

2. **Download required model files**
   - See `backend/MODELS.md` for detailed instructions
   - Models are not included in the repository due to size constraints
   - Place downloaded models in the `backend/` directory

3. **Navigate to backend directory**
   ```bash
   cd backend
   ```

4. **Download model files** (see MODELS.md for details)
   ```bash
   # Example for Dlib model:
   wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
   bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
   ```

5. **Create Conda environment** (recommended)
   ```bash
   conda env create -f environment.yml
   conda activate fatigue-detection
   ```

   Or **install with pip**:
   ```bash
   pip install flask opencv-python ultralytics dlib torch torchvision
   ```

6. **Run the Flask application**
   ```bash
   python app.py
   ```

7. **Access the application**
   - Open browser: `http://localhost:5000`
   - Use webcam for real-time detection
   - Upload videos for analysis

---

## 📖 Usage

### Helmet Detection
1. Navigate to the Helmet Detection page
2. Choose input source:
   - Webcam for live detection
   - Upload video file
   - Provide video URL
3. View real-time detection results with bounding boxes

### Fatigue Detection
1. Navigate to the Fatigue Detection page
2. Select video source (webcam/upload/URL)
3. System analyzes:
   - Eye closure (EAR)
   - Head pose angles
   - Yawning frequency
4. Alerts triggered when fatigue score > 0.50

---

## 🎨 GitHub Pages Website

The static website in the `docs/` folder provides:
- Project overview and features
- Detailed information about AI models
- FAQ section
- Contact and demo request forms

To enable GitHub Pages:
1. Go to repository Settings
2. Navigate to Pages section
3. Select `main` branch and `/docs` folder
4. Save and wait for deployment

---

## 🧪 Model Information

### Helmet Detection Model
- **Framework**: YOLOv8
- **Model**: Custom trained on helmet safety dataset
- **Location**: `backend/AIHelmet/best.pt`

### Fatigue Detection Models
- **Swin Transformer**: Visual fatigue analysis (60% weight)
- **Geometric Analysis**: EAR and head pose (40% weight)
- **Face Landmarks**: Dlib 68-point model
- **Models**: `swin_best.pth`, `shape_predictor_68_face_landmarks.dat`

---

## 📊 Dataset

The project uses a custom dataset from SUT El Sewedy University for training and validation.

---

## 🤝 Contributing

This is a student project for El Sewedy University of Technology. Contributions and feedback are welcome!

---

## 📄 License

This project is developed as part of academic coursework at SUT El Sewedy University.

---

## 👥 Team

Student project by the AI & Computer Vision team at El Sewedy University of Technology.

---

## 📞 Contact

For inquiries, demos, or collaboration:
- Visit our [Contact Page](docs/contact.html)
- Submit a [Demo Request](docs/demo.html)

---

**⚠️ Safety Note**: This system is designed to assist in workplace safety monitoring but should not replace proper safety protocols and human supervision.
