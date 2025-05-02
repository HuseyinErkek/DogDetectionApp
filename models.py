# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Cameras(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)

class DetectionCameraInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'))
    detectionTime = db.Column(db.DateTime, server_default=db.func.now())
    confidence = db.Column(db.Float)
    camera = db.relationship('Cameras', backref=db.backref('detections', lazy=True))


class DetectionUploadedVideoInfo(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('detection_camera_info.id'), primary_key=True)
    video_id = db.Column(db.Integer, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    total_people = db.Column(db.Integer)
    total_dog = db.Column(db.Integer)
    confidence = db.Column(db.Float)
    status = db.Column(db.String(255), nullable=False)
    detectionTime = db.Column(db.DateTime, server_default=db.func.now())
    camera_info = db.relationship('DetectionCameraInfo', backref=db.backref('uploaded_videos', lazy=True))

class SegmentStatistic(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    detectionTime = db.Column(db.DateTime, server_default=db.func.now())
    total_dog = db.Column(db.Integer)
    total_people = db.Column(db.Integer)

#-------------------------------
# Object Model (Köpek veya Person gibi nesneleri tanımlar)
class Object(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    object_type = db.Column(db.String(50), nullable=False)  # 'person', 'dog' vs.
    detections = db.relationship('Detection', backref='object', lazy=True)

# Detection Model (Her tespiti temsil eder)
class Detection(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)  # Görüntü dosyası adı
    detection_time = db.Column(db.DateTime, nullable=False)  # Tespit zamanı
    object_id = db.Column(db.Integer, db.ForeignKey('object.id'), nullable=False)  # İlgili nesnenin ID'si