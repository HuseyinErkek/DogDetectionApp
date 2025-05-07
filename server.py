import os
import threading
import uuid
from flask import render_template, request, redirect, url_for
from flask_socketio import emit
from werkzeug.utils import secure_filename

from app_init import DogDetec, DB_NAME, UPLOAD_FOLDER, socketio, create_database, db
from process_uploaded_video import VideoProcessor
from settings import ProcessingSettings, ModelSettings

@DogDetec.route('/')
def home():
    return render_template("index.html")

@DogDetec.route('/city/<city_name>')
def city_cameras(city_name):
    cities = {
        "bursa": [
            {"name": "Osmangazi", "image_url": "/static/images/osmangazi.jpg"},
            {"name": "Nilüfer", "image_url": "/static/images/nilufer.jpg"},
            {"name": "Yıldırım", "image_url": "/static/images/yildirim.jpg"}
        ],
        "izmir": [
            {"name": "Konak", "image_url": "/static/images/konak.jpg"},
            {"name": "Bornova", "image_url": "/static/images/bornova.jpg"},
            {"name": "Karşıyaka", "image_url": "/static/images/karsiyaka.jpg"}
        ],
        "istanbul": [
            {"name": "Kadıköy", "image_url": "/static/images/kadikoy.jpg"},
            {"name": "Beşiktaş", "image_url": "/static/images/besiktas.jpg"},
            {"name": "Üsküdar", "image_url": "/static/images/uskudar.jpg"}
        ]
    }

    districts = cities.get(city_name.lower(), [])
    return render_template("camera.html", city_name=city_name, districts=districts)

@DogDetec.route('/howto')
def howto():
    return render_template("howto.html")

@DogDetec.route('/camera')
def camera():
    return render_template("camera.html")

@DogDetec.route('/upload', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        if 'video' not in request.files:
            return redirect(request.url)

        file = request.files['video']
        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = str(uuid.uuid4()) + secure_filename(file.filename)
            filepath = os.path.join(DogDetec.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            settings = ProcessingSettings()
            model_settings = ModelSettings()
            video_processor = VideoProcessor(settings, model_settings, socketio)
            threading.Thread(target=video_processor.process_video_periodic, args=(filepath, filename)).start()

            return redirect(url_for('processing'))
    return render_template('upload.html')

@DogDetec.route('/processing')
def processing():
    return render_template('processing.html')

@DogDetec.route('/upload_success')
def upload_success():
    return render_template('upload_succes.html')

@socketio.on('connect')
def handle_connect():
    print("Web socket baglandi")
    emit('server_message', {'message': 'Soket bağlandı!!!'})

@socketio.on('disconnect')
def handle_disconnect():
    print("WebSocket bağlantısı kesildi")

@socketio.on('progress')
def handle_progress(data):
    print("Web soket progress icin kisim acildi")
    emit('progress', data)

if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        with DogDetec.app_context():
            db.create_all()
        print("Veritabanı oluşturuldu.")
    else:
        print("Veritabanı zaten mevcut.")

    socketio.run(DogDetec, debug=True, allow_unsafe_werkzeug=True)
