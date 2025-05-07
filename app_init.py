import os
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

# Yapılandırma değişkenlerini tanımlıyoruz
UPLOAD_FOLDER = 'uploads'
DB_NAME = "dogdetection.db"
SECRET_KEY = '1234asd'

# Flask uygulamasını oluşturuyoruz
DogDetec = Flask(__name__, static_folder='static', template_folder='templates')

# Yapılandırmayı Flask uygulamasına yüklüyoruz
DogDetec.config['SECRET_KEY'] = SECRET_KEY
DogDetec.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
DogDetec.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Gerekli klasörü oluşturuyoruz
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# SQLAlchemy ve SocketIO nesnelerini oluşturuyoruz
db = SQLAlchemy(DogDetec)
socketio = SocketIO(DogDetec,cors_allowed_origins="*")

# Veritabanı oluşturma fonksiyonu
def create_database():
    """Uygulama bağlamında veritabanını oluşturur."""
    with DogDetec.app_context():
        db.create_all()
    print("Veritabanı oluşturuldu.")

