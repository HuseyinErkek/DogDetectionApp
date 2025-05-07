
import os
import threading
import uuid
from flask import render_template, request, redirect, url_for
from flask_socketio import emit

from werkzeug.utils import secure_filename

from app_init import DogDetec, DB_NAME, UPLOAD_FOLDER, socketio,create_database
from process_uploaded_video import VideoProcessor
from settings import ProcessingSettings, ModelSettings

@DogDetec.route('/')
def home():
    return render_template("index.html")


@DogDetec.route('/camera')
def camera():
    return render_template("camera.html")

@DogDetec.route('/howto')
def howto():
    return render_template("howto.html")

# Video yükleme işlemleri için route  tanımı (GET ve POST metotlarını kabul eder)
@DogDetec.route('/upload', methods=['GET', 'POST'])
def upload_video():
    """
    GET isteği: Video yükleme formunu (upload.html) gösterir.
    POST isteği: Yüklenen video dosyasını işler.
    """
    if request.method == 'POST':
        # Formda 'video' adında bir dosya olup olmadığını kontrol ediyoruz
        if 'video' not in request.files:
            return redirect(request.url)  # Eğer yoksa aynı sayfaya geri yönlendiriyoruz

        file = request.files['video']  # Yüklenen video dosyasını alıyoruz
        if file.filename == '':
            return redirect(request.url)  # Eğer dosya adı boşsa aynı sayfaya geri yönlendiriyoruz

        if file:
            filename = str(uuid.uuid4()) + secure_filename(file.filename)
            filepath = os.path.join(DogDetec.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Video işleme fonksiyonunu ayrı bir thread'de başlatıyoruz
            settings = ProcessingSettings()
            model_settings = ModelSettings()
            video_processor = VideoProcessor(settings, model_settings,socketio)
            threading.Thread(target=video_processor.process_video_periodic, args=(filepath, filename)).start()
            #Video işleniyor sayfasına gönderiyoruz.
            return redirect(url_for('processing'))
    # GET isteği durumunda video yükleme formunu gösteriyoruz
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

# WebSocket bağlantısı kesildiğinde çalışacak fonksiyon
@socketio.on('disconnect')
def handle_disconnect():
    print("WebSocket bağlantısı kesildi")

@socketio.on('progress')
def handle_progress(data):
    print("Web soket progress icin kisim acildi")
    emit('progress', data)

if __name__ == '__main__':
    # Veritabanı dosyasının varlığını kontrol ederek gerekirse oluşturuyoruz
    if not os.path.exists(DB_NAME):
        create_database()
    else:
        print("Veritabanı zaten mevcut.")

    # SocketIO ile Flask uygulamasını başlatıyoruz
    socketio.run(DogDetec,debug=True,allow_unsafe_werkzeug=True)
