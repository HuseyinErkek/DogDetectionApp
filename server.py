import os
import threading
import uuid

from flask import render_template, request, redirect, url_for, session, jsonify
from flask_socketio import leave_room, emit, join_room
from werkzeug.utils import secure_filename

from app_init import DogDetec, DB_NAME, socketio, db
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

@DogDetec.route('/city/<city_name>/<district_name>')
def district_camera(city_name, district_name):
    return render_template('district_camera.html', city_name=city_name, district_name=district_name)


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
            session_id= request.form.get("sessionIdInput")
            threading.Thread(target=video_processor.process_video_periodic, args=(filepath, filename, session_id)).start() # request.sid kullanın

            return redirect(url_for('processing'))
    return render_template('upload.html')

@DogDetec.route('/processing')
def processing():
    return render_template('processing.html')

@DogDetec.route('/upload_success')
def upload_success():
    return render_template('upload_succes.html')

connected_clients = {}

@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    connected_clients[session_id] = True
    print(f"Yeni bağlantı: {session_id}")
    emit('session_id', {'sessionId': session_id})
    join_room(session_id) # Bağlanır bağlanmaz odaya al


@socketio.on('progress')
def handle_progress(data):
    session_id = data.get('sessionId')
    progress = data.get('progress')

    if progress is not None:
        emit('progress', {'progress': progress}, to=session_id)
    else:
        print(f"Hata (progress): Geçersiz progress değeri - {session_id}")

@socketio.on('segment_progress')
def handle_segment_progress(data):
    session_id = data.get('sessionId')
    segment_progress = data.get('segment_progress')

    if segment_progress is not None:
        emit('segment_progress', {'segment_progress': segment_progress}, to=session_id)
    else:
        print(f"Hata (segment): Geçersiz segment_progress değeri - {session_id}")

@socketio.on('wait_timer')
def handle_wait_timer(data):
    session_id = data.get('sessionId')
    remaining_seconds = data.get('remaining_seconds') # Kalan süreyi al
    if remaining_seconds is not None:
        emit('wait_timer', {'remaining_seconds': remaining_seconds}, to=session_id)
    else:
        print(f"Hata (timer): Geçersiz remaining_seconds değeri - {session_id}")


@socketio.on('leave_room')
def handle_leave(data):
    session_id = data.get('sessionId')
    if session_id:
        leave_room(session_id)
        print(f"{session_id} odasından çıkıldı.")


@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in connected_clients:
        del connected_clients[session_id]
    print(f"WebSocket bağlantısı kesildi: {session_id}")
    leave_room(session_id) # Bağlantı kesilince odadan çık


if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        with DogDetec.app_context():
            db.create_all()
        print("Veritabanı oluşturuldu.")
    else:
        print("Veritabanı zaten mevcut.")

    socketio.run(DogDetec, debug=True, allow_unsafe_werkzeug=True)