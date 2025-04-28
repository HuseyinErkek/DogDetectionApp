# main.py veya uygulamanızın ana dosyası
import os
from flask import Flask, render_template
from datetime import datetime

# models.py dosyasındaki db ve modelleri içeri aktarıyoruz
from models import db, Cameras, DetectionInfo

# Veritabanı adı
DB_NAME = "dogdetection.db"

# Flask uygulamasını başlatıyoruz
DogDetec = Flask(__name__)

# Flask konfigürasyonlarını ayarlıyoruz
DogDetec.config['SECRET_KEY'] = '1234asd'
DogDetec.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
DogDetec.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Bu ayar önerilir, gereksiz bildirimlerden kaçınmak için

# SQLAlchemy bağlantısını başlatıyoruz
db.init_app(DogDetec)

# Anasayfa route
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

@DogDetec.route('/upload.html')
def upload():
    return render_template("upload.html")

# Uygulama başlatıldığında veritabanını kontrol et
if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        # Flask uygulama bağlamı içinde veritabanı oluşturma işlemi
        with DogDetec.app_context():
            db.create_all()
        print("Database created")
    else:
        print("Database already exists")

    # Flask uygulamasını çalıştırıyoruz
    DogDetec.debug = True
    DogDetec.run()
