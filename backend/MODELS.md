# Model Files

Due to GitHub's file size limitations, the following large model files are not included in this repository:

## Required Model Files

### 1. **YOLOv8 Helmet Detection Model**
- **File**: `best.pt`
- **Location**: `backend/AIHelmet/best.pt`
- **Size**: ~6-10 MB
- **Description**: Custom-trained YOLOv8 model for helmet detection

### 2. **Dlib Face Landmarks Model**
- **File**: `shape_predictor_68_face_landmarks.dat`
- **Location**: `backend/shape_predictor_68_face_landmarks.dat`
- **Size**: ~95 MB
- **Download**: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
- **Description**: Pre-trained 68-point facial landmark detector

### 3. **Swin Transformer Fatigue Model**
- **File**: `swin_best.pth`
- **Location**: `backend/swin_best.pth`
- **Size**: ~188 MB
- **Description**: Custom-trained Swin Transformer for fatigue detection

## Installation Instructions

1. **Download the models** from the sources above or contact the project maintainer
2. **Extract** (if compressed) and place them in the correct locations:
   ```
   backend/
   ├── AIHelmet/
   │   └── best.pt                              ← Place here
   ├── shape_predictor_68_face_landmarks.dat    ← Place here
   └── swin_best.pth                            ← Place here
   ```

3. **Verify** the files are in place before running the Flask application

## Alternative: Git LFS

If you want to include these files in git, consider using [Git Large File Storage (LFS)](https://git-lfs.github.com/):

```bash
git lfs install
git lfs track "*.pt"
git lfs track "*.pth"
git lfs track "*.dat"
```

## Notes

- The Flask application will still run without these files, but detection features will be disabled
- Check the console output when starting the app for model loading status
- For the Dlib model, you can download and extract it using:
  ```bash
  cd backend
  wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
  bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
  ```
