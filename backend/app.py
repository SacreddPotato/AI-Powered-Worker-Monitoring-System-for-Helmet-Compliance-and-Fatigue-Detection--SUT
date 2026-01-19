import os
import cv2
from flask import Flask, render_template, Response, request, redirect, url_for
from werkzeug.utils import secure_filename
from camera import VideoCamera
from helmet_camera import HelmetCamera
from huggingface_hub import hf_hub_download
from pathlib import Path

base_dir = os.path.dirname(os.path.abspath(__file__))
docs_folder = os.path.join(base_dir, '..', 'docs')

# Point Flask to use 'docs' for both templates and static files
app = Flask(__name__, 
            template_folder=docs_folder, 
            static_folder=docs_folder, 
            static_url_path='')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- PAGE ROUTES ---
@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/fatigue.html')
def fatigue():
    return render_template('fatigue.html')

@app.route('/helmet.html')
def helmet():
    return render_template('helmet.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')

@app.route('/demo.html')
def demo():
    return render_template('demo.html')

@app.route('/faq.html')
def faq():
    return render_template('faq.html')

# --- VIDEO STREAM LOGIC ---
def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else: break

@app.route('/video_feed')
def video_feed():
    source = request.args.get('source', '0')
    # If source is '0', use webcam. Otherwise use file path.
    if source == '0':
        return Response(gen(VideoCamera(source=0)), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(gen(VideoCamera(source=source)), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- UPLOAD HANDLE (Fixes 405 Error) ---
@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            # Return JSON response instead of redirect
            return {'success': True, 'filename': filename, 'path': path}, 200
    return {'success': False, 'error': 'No file provided'}, 400

# --- HELMET VIDEO STREAM LOGIC ---
def gen_helmet(camera):
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            break

@app.route('/helmet_video_feed')
def helmet_video_feed():
    source = request.args.get('source', '0')
    # If source is '0', use webcam. Otherwise use file path.
    if source == '0':
        return Response(gen_helmet(HelmetCamera(source=0)), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(gen_helmet(HelmetCamera(source=source)), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- HELMET UPLOAD HANDLE ---
@app.route('/upload_helmet_video', methods=['POST'])
def upload_helmet_video():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            # Return JSON response instead of redirect
            return {'success': True, 'filename': filename, 'path': path}, 200
    return {'success': False, 'error': 'No file provided'}, 400


def check_and_download_models():
    """
    Robust version: Uses absolute paths to check for models, ignoring 
    where the command was run from.
    """
    repo_id = "SacreddPotato/worker-monitoring-system"
    
    # Calculate the absolute paths dynamically
    # backend_dir = The folder containing THIS file (app.py)
    backend_dir = Path(__file__).resolve().parent
    
    # project_root = The folder above backend (where Dockerfile lives)
    project_root = backend_dir.parent

    print(f"[INFO] Project Root detected at: {project_root}")

    # Map Repo filenames to their Absolute Local Paths
    files_map = {
        "backend/best.pt": project_root / "backend" / "best.pt",
        "backend/swin_best.pth": project_root / "backend" / "swin_best.pth",
        "backend/shape_predictor_68_face_landmarks.dat": project_root / "backend" / "shape_predictor_68_face_landmarks.dat",
        "backend/yolov8n.pt": project_root / "backend" / "yolov8n.pt"
    }

    print(f"[INFO] Initializing model verification for: {repo_id}")

    for repo_path, local_abs_path in files_map.items():
        # 1. Check if file exists (using absolute path)
        if local_abs_path.exists():
            # 2. Check size (MB)
            file_size_mb = local_abs_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb > 0.01: # larger than ~10KB
                print(f"[INFO] Found local file: {local_abs_path.name} ({file_size_mb:.2f} MB). Skipping.")
                continue 
            else:
                print(f"[WARNING] Invalid LFS pointer found: {local_abs_path.name}. Redownloading...")
        else:
            print(f"[WARNING] Missing file: {local_abs_path.name}. Starting download...")

        # 3. Download if missing/broken
        try:
            # We download to project_root so 'backend/file' lands in 'project_root/backend/file'
            hf_hub_download(
                repo_id=repo_id,
                filename=repo_path,
                repo_type="space",
                local_dir=project_root,  # FORCE download to the absolute root path
                local_dir_use_symlinks=False
            )
            print(f"[SUCCESS] Downloaded: {repo_path}")
            
        except Exception as e:
            print(f"[ERROR] Failed to download {repo_path}: {e}")

if __name__ == '__main__':
    check_and_download_models()
    
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=7860, debug=debug_mode, threaded=True)