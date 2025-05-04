import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy



# Flask uygulamasını başlatıyoruz
DogDetec = Flask(__name__,static_folder='static',template_folder='templates')
UPLOAD_FOLDER = 'uploads'
# Veritabanı dosyasının adını tanımlıyoruz
DB_NAME = "dogdetection.db"

# Flask uygulamasının yapılandırmasını ayarlıyoruz
DogDetec.config['SECRET_KEY'] = '1234asd'  # Uygulama için gizli anahtar
DogDetec.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'  # Veritabanı bağlantı URI'si
DogDetec.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(DogDetec)


