
import os
import threading
import uuid
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

from app_init import DogDetec,db,DB_NAME,UPLOAD_FOLDER
from process_uploaded_video import VideoProcessor
from settings import ProcessingSettings, ModelSettings


# Yüklenen videolar için klasörü oluşturuyoruz (eğer yoksa)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
            video_processor = VideoProcessor(settings, model_settings)

            threading.Thread(target=video_processor.process_video_periodic, args=(filepath, filename)).start()

            return redirect(url_for('upload_success'))
    # GET isteği durumunda video yükleme formunu gösteriyoruz
    return render_template('upload.html')

@DogDetec.route('/upload_success')
def upload_success():
    return render_template('upload_succes.html')


# Uygulama ilk kez çalıştırıldığında veritabanını oluşturma kontrolü
if __name__ == '__main__':
    # Veritabanı dosyasının var olup olmadığını kontrol ediyoruz
    if not os.path.exists(DB_NAME):
        # Flask uygulama bağlamı içinde veritabanını oluşturuyoruz
        with DogDetec.app_context():
            db.create_all()
        print("Veritabanı oluşturuldu.")
    else:
        print("Veritabanı zaten mevcut.")

    # Flask uygulamasını geliştirme modunda (debug=True) çalıştırıyoruz
    DogDetec.debug = False
    DogDetec.run() # Tüm ağlardan erişilebilir hale getiriyoruz (isteğe bağlı)