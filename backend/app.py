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
        
        if helmet_model is not None:
            # Run YOLO inference
            results = helmet_model(frame, conf=0.5, verbose=False)
            frame = results[0].plot()
        
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