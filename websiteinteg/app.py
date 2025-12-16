import os
from flask import Flask, render_template, Response, request, redirect, url_for
from werkzeug.utils import secure_filename
from camera import VideoCamera

# FIX: Point Flask to the 'website' folder for HTML, CSS, and JS
app = Flask(__name__, template_folder='website', static_folder='website', static_url_path='')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- PAGE ROUTES ---
@app.route('/')
@app.route('/index.html')
def index():
    return render_template('Index.html')

@app.route('/fatigue.html')
def fatigue():
    return render_template('Fatigue.html')

@app.route('/helmet.html')
def helmet():
    return render_template('Helmet.html')

@app.route('/about.html')
def about():
    return render_template('About.html')

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)