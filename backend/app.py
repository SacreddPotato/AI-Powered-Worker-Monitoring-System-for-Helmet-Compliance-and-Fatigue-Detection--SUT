import os
import cv2
from flask import Flask, render_template, Response, request, redirect, url_for
from werkzeug.utils import secure_filename
from camera import VideoCamera
from ultralytics import YOLO

# Point Flask to the templates folder for backend templates
# For the static website, use the docs/ folder served by GitHub Pages
app = Flask(__name__, template_folder='templates', static_folder='templates', static_url_path='')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load helmet detection model
HELMET_MODEL_PATH = os.path.join(os.path.dirname(__file__), "AIHelmet", "best.pt")
helmet_model = None
if os.path.exists(HELMET_MODEL_PATH):
    helmet_model = YOLO(HELMET_MODEL_PATH)
    print(f"[INFO] Helmet model loaded from {HELMET_MODEL_PATH}")
else:
    print(f"[WARNING] Helmet model not found at {HELMET_MODEL_PATH}")

# Load standard YOLOv8 model for Person Detection
# This is more reliable than face detection for workers facing away
try:
    # This will automatically download yolov8n.pt (approx 6MB) on first run
    person_model = YOLO('yolov8n.pt')
    print("[INFO] Person detection model (yolov8n.pt) loaded.")
except Exception as e:
    print(f"[WARNING] Could not load yolov8n.pt: {e}")
    person_model = None

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
            # Redirect back to Fatigue page with the video source
            return redirect(url_for('fatigue', source=path))
    return redirect(url_for('fatigue'))

# --- HELMET VIDEO STREAM LOGIC ---
def gen_helmet(source):
    video = cv2.VideoCapture(source)
    while True:
        success, frame = video.read()
        if not success:
            break
        
        # Lists to store detection coordinates
        helmet_boxes = []

        # 1. Detect Helmets (Custom YOLO)
        if helmet_model is not None:
            # Run YOLO inference
            results = helmet_model(frame, conf=0.5, verbose=False)
            
            # Draw Helmets (Green)
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0]
                helmet_boxes.append((x1, y1, x2, y2))
                
                # Draw Green Box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Helmet {conf:.2f}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 2. Detect People (Standard YOLOv8)
        # We use this to find workers who are NOT wearing helmets
        if person_model is not None:
            # Detect only class 0 (person)
            results_person = person_model(frame, classes=[0], conf=0.5, verbose=False)
            
            for box in results_person[0].boxes:
                px1, py1, px2, py2 = map(int, box.xyxy[0])
                
                # Check if this person has a corresponding helmet
                has_helmet = False
                
                for (hx1, hy1, hx2, hy2) in helmet_boxes:
                    # Logic: Check for intersection or close proximity
                    
                    # 1. Calculate intersection rectangle
                    ix1 = max(px1, hx1)
                    iy1 = max(py1, hy1)
                    ix2 = min(px2, hx2)
                    iy2 = min(py2, hy2)
                    
                    intersection_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                    
                    # If there is significant overlap (helmet is on the person)
                    if intersection_area > 0:
                        has_helmet = True
                        break
                    
                    # 2. Alternative Logic: Check if helmet is "floating" just above the person
                    # (Sometimes the person box cuts off at the forehead, but helmet sits higher)
                    h_center_x = (hx1 + hx2) // 2
                    h_bottom_y = hy2
                    
                    # If helmet is horizontally aligned with person
                    if px1 < h_center_x < px2:
                        # And helmet is near the top of the person box (within 20% of person height)
                        person_height = py2 - py1
                        if abs(h_bottom_y - py1) < (person_height * 0.2): 
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
    # If source is '0', use webcam. Otherwise use file path.
    if source == '0':
        return Response(gen_helmet(0), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(gen_helmet(source), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- HELMET UPLOAD HANDLE ---
@app.route('/upload_helmet_video', methods=['POST'])
def upload_helmet_video():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            # Redirect back to Helmet page with the video source
            return redirect(url_for('helmet', source=path))
    return redirect(url_for('helmet'))

if __name__ == '__main__':
    # Note: Set debug=False in production environments
    # For development, you can set debug=True to enable auto-reload and detailed error pages
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode, threaded=True)