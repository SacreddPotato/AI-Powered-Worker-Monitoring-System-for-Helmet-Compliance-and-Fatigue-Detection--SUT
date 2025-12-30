import os
import cv2
from flask import Flask, render_template, Response, request, redirect, url_for
from werkzeug.utils import secure_filename
from camera import VideoCamera
from ultralytics import YOLO

# Point Flask to the templates folder
app = Flask(__name__, template_folder='templates', static_folder='templates', static_url_path='')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- MODEL LOADING WITH POINTER/PICKLE PROTECTION ---

def load_or_download_model(model_path, is_standard_yolo=False):
    """
    Checks if a model file is a valid binary or a Git LFS pointer.
    If it's a pointer (small file) and it's a standard YOLO model, 
    delete it to trigger a fresh download.
    """
    if os.path.exists(model_path):
        # Check file size. LFS pointers are usually < 1KB (approx 130 bytes).
        # Real YOLOv8n is ~6MB.
        file_size_kb = os.path.getsize(model_path) / 1024
        
        if file_size_kb < 10: # If less than 10KB, it's likely a pointer/corrupt
            print(f"[INFO] Detected LFS pointer or empty file for {model_path} ({file_size_kb:.2f} KB).")
            if is_standard_yolo:
                print(f"[INFO] Deleting {model_path} to re-download valid weight...")
                try:
                    os.remove(model_path)
                except OSError as e:
                    print(f"[ERROR] Error deleting file: {e}")
            else:
                print(f"[WARNING] Custom model {model_path} seems to be an LFS pointer. Please ensure Git LFS pulled the real file.")
    
    try:
        # If file is missing (deleted above) or present, YOLO() handles loading/downloading
        model = YOLO(model_path)
        print(f"[INFO] Successfully loaded model: {model_path}")
        return model
    except Exception as e:
        print(f"[ERROR] Failed to load model {model_path}: {e}")
        return None

# 1. Load Custom Helmet Model
HELMET_MODEL_PATH = os.path.join("AIHelmet", "best.pt")
helmet_model = load_or_download_model(HELMET_MODEL_PATH, is_standard_yolo=False)

# 2. Load Standard Person Model (yolov8n.pt)
# We set is_standard_yolo=True so it auto-deletes pointers and downloads the real one
person_model = load_or_download_model('yolov8n.pt', is_standard_yolo=True)


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
    if source == '0':
        return Response(gen(VideoCamera(source=0)), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(gen(VideoCamera(source=source)), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- UPLOAD HANDLE ---
@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            return redirect(url_for('fatigue', source=path))
    return redirect(url_for('fatigue'))

# --- HELMET VIDEO STREAM LOGIC (Updated with "Helmet Not Found") ---
def gen_helmet(source):
    # Handle webcam index vs file path
    if source == '0' or source == 0:
        video = cv2.VideoCapture(0)
    else:
        video = cv2.VideoCapture(source)
        
    while True:
        success, frame = video.read()
        if not success:
            break
        
        # Lists to store detection coordinates
        helmet_boxes = []

        # 1. Detect Helmets (Custom YOLO)
        if helmet_model is not None:
            results = helmet_model(frame, conf=0.5, verbose=False)
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0]
                helmet_boxes.append((x1, y1, x2, y2))
                
                # Draw Green Box for Helmet
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Helmet {conf:.2f}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 2. Detect People (Standard YOLOv8n) to find missing helmets
        if person_model is not None:
            # Detect only class 0 (person)
            results_person = person_model(frame, classes=[0], conf=0.5, verbose=False)
            
            for box in results_person[0].boxes:
                px1, py1, px2, py2 = map(int, box.xyxy[0])
                
                # Check if this person has a corresponding helmet
                has_helmet = False
                
                for (hx1, hy1, hx2, hy2) in helmet_boxes:
                    # Intersection logic
                    ix1 = max(px1, hx1)
                    iy1 = max(py1, hy1)
                    ix2 = min(px2, hx2)
                    iy2 = min(py2, hy2)
                    
                    intersection_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                    
                    if intersection_area > 0:
                        has_helmet = True
                        break
                    
                    # Proximity logic (Helmet sitting on head)
                    h_center_x = (hx1 + hx2) // 2
                    if px1 < h_center_x < px2:
                        # If helmet bottom is near person top
                        person_height = py2 - py1
                        if abs(hy2 - py1) < (person_height * 0.25): 
                            has_helmet = True
                            break

                if not has_helmet:
                    # Draw Red Box for No Helmet
                    cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 0, 255), 2)
                    cv2.putText(frame, "HELMET NOT FOUND", (px1, py1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    video.release()

@app.route('/helmet_video_feed')
def helmet_video_feed():
    source = request.args.get('source', '0')
    if source == '0':
        return Response(gen_helmet(0), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(gen_helmet(source), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload_helmet_video', methods=['POST'])
def upload_helmet_video():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            return redirect(url_for('helmet', source=path))
    return redirect(url_for('helmet'))

if __name__ == '__main__':
    # Set debug=False for production/HF Spaces
    app.run(host='0.0.0.0', port=7860, debug=False)
