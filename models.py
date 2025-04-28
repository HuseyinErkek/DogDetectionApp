# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Cameras(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)

class DetectionInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'))
    detectionTime = db.Column(db.DateTime, server_default=db.func.now())
    confidence = db.Column(db.Float)
    camera = db.relationship('Cameras', backref=db.backref('detections', lazy=True))
