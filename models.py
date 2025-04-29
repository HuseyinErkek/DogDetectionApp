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
    id = db.Column(db.Integer, db.ForeignKey('DetectionCameraInfo.id'),autoincrement=True)
    video_id = db.Column(db.Integer,autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    total_people = db.Column(db.Integer)
    total_dog = db.Column(db.Integer)
    confidence = db.Column(db.Float)
    status = db.Column(db.String(255), nullable=False)
    detectionTime = db.Column(db.DateTime, server_default=db.func.now())

