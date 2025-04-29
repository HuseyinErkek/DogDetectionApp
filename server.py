
import os
import threading
import uuid



# Flask ve ilgili araçları içe aktarıyoruz
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

# Veritabanı modellerini içeren 'models.py' dosyasını içe aktarıyoruz
from models import db, Cameras, DetectionCameraInfo
from video_processing import process_uploaded_video

# Yüklenen videolar için klasörü oluşturuyoruz (eğer yoksa)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Veritabanı dosyasının adını tanımlıyoruz
DB_NAME = "dogdetection.db"

# Flask uygulamasını başlatıyoruz
DogDetec = Flask(__name__)

# Flask uygulamasının yapılandırmasını ayarlıyoruz
DogDetec.config['SECRET_KEY'] = '1234asd'  # Uygulama için gizli anahtar
DogDetec.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'  # Veritabanı bağlantı URI'si
DogDetec.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# SQLAlchemy kütüphanesini Flask uygulamasına bağlıyoruz
db.init_app(DogDetec)


@DogDetec.route('/')
def home():
    return render_template('index.html')

@DogDetec.route('/index.html')
def index():
    return render_template('index.html')

@DogDetec.route('/camera.html')
def camera():
    return render_template('camera.html')

@DogDetec.route('/howto.html')
def howto():
    return render_template("howto.html")

# Video yükleme işlemleri için route tanımı (GET ve POST metotlarını kabul eder)
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
            # Güvenli bir dosya adı oluşturuyoruz (benzersiz ID ile birlikte)
            filename = str(uuid.uuid4()) + secure_filename(file.filename)
            # Dosyanın kaydedileceği tam yolu oluşturuyoruz
            filepath = os.path.join(DogDetec.config['UPLOAD_FOLDER'], filename)
            # Dosyayı belirtilen konuma kaydediyoruz
            file.save(filepath)

            # Yüklenen videoyu işleyecek bir fonksiyonu ayrı bir thread'de başlatıyoruz
            threading.Thread(target=process_uploaded_video,
                             args=(filepath, filename)).start()

            # Yükleme başarılı olduktan sonra 'upload' sayfasına yeniden yönlendiriyoruz
            return redirect(url_for('upload_success'))
    # GET isteği durumunda video yükleme formunu gösteriyoruz
    return render_template('upload.html')

@DogDetec.route('/upload/success')
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
    DogDetec.debug = True
    DogDetec.run() # Tüm ağlardan erişilebilir hale getiriyoruz (isteğe bağlı)