from app_init import *
from datetime import datetime
from models import db, Object, Detection
import traceback

def detect_object(model_object_id, object_type, filename):
    try:
        # Flask uygulama bağlamını başlatıyoruz
        with DogDetec.app_context():
            # Modelin verdiği model_object_id’ye göre veritabanında nesne arama
            existing_object = Object.query.filter_by(model_object_id=model_object_id).first()

            # Eğer nesne daha önce tespit edilmemişse kaydet
            if not existing_object:
                existing_object = Object(model_object_id=model_object_id, object_type=object_type)
                db.session.add(existing_object)
                db.session.commit()

            # Detection kaydını kontrol et, aynı nesne için aynı dosyada daha önce tespit yapılmış mı
            existing_detection = Detection.query.filter_by(
                object_id=existing_object.model_object_id,
                filename=filename
            ).first()

            if existing_detection:
                # Zaten tespit edilmişse zamanı güncelle
                existing_detection.detection_time = datetime.utcnow()
            else:
                # Yeni bir tespit oluştur
                new_detection = Detection(
                    object_id=existing_object.model_object_id,
                    filename=filename,
                    detection_time=datetime.utcnow()
                )
                db.session.add(new_detection)

            db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Hata oluştu: {e}")
        traceback.print_exc()
