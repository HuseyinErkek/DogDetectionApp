import sqlite3
import os
from ultralytics import YOLO
from dbmaneger import init_db, log_to_db

# YOLOv8 model yolu
MODEL_PATH = 'model/yolov8m_epochs50.pt'

# Takip edilecek sınıflar
CLASS_NAMES = {
    0: 'person',
    16: 'dog'
}

def process_uploaded_video(filepath, filename):
    # Modeli yükle
    model = YOLO(MODEL_PATH)

    # Veritabanı bağlantısı
    conn = init_db()

    # Çıktı klasörü
    output_dir = os.path.join(os.path.dirname(filepath), 'processed_videos')
    os.makedirs(output_dir, exist_ok=True)

    # Takip işlemi
    results = model.track(
        source=filepath,
        stream=True,
        conf=0.5,
        iou=0.5,
        persist=True,
        save=True,
        project=output_dir,
        name="takip_sonucu",
        tracker="botsort.yaml"
    )

    # Toplam insan ve köpek ID'lerini sakla
    people_ids = set()
    dog_ids = set()

    # Tüm frameleri gez
    for r in results:
        if r.boxes.id is not None:
            ids = r.boxes.id.cpu().tolist()
            classes = r.boxes.cls.cpu().tolist()

            for obj_id, cls in zip(ids, classes):
                if int(cls) == 0:
                    people_ids.add(int(obj_id))
                elif int(cls) == 16:
                    dog_ids.add(int(obj_id))

    # Sayıları al
    total_people = len(people_ids)
    total_dogs = len(dog_ids)

    # Veritabanına kaydet
    log_to_db(conn, filename, total_people, total_dogs, 0.0, "")
    conn.close()

    print(f"Takip tamamlandı. İnsan: {total_people}, Köpek: {total_dogs}")
