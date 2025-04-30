import sqlite3
import cv2
from mypyc.doc.conf import project
from ultralytics import YOLO
import os

from ultralytics.trackers.utils.matching import iou_distance

from dbmaneger import init_db, log_to_db


# YOLOv8 model yolu
MODEL_PATH = 'model/yolov8m_epochs50.pt'

# Nesne sınıfları (COCO dataset class IDs)
CLASS_NAMES = {
    0: 'person',
    16: 'dog'
}

def process_uploaded_video(filepath, filename):
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        raise ValueError("Video dosyası açılamadı. Lütfen yolu kontrol edin.")

    # FPS kontrolü
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 25  # varsayılan fps atanabilir

    # Model yükleme
    model = YOLO(MODEL_PATH)

    result = model.track(
        source=0,
        conf=0.5,
        persist=True,
        show=True,
        save=False,
        project="proccessed_video",
        name="takip_sonucu"
    )

    # Veritabanı bağlantısı
    conn = init_db()

    # Çıktı dosya yolu
    output_dir = os.path.join(os.path.dirname(filepath), 'processed_videos')
    os.makedirs(output_dir, exist_ok=True)
    output_video_path = os.path.join(output_dir, filename)

    # Çıktı görüntü dosya ayarları
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    total_people = 0
    total_dogs = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        boxes = results[0].boxes
        detected_objects = boxes.data.cpu().numpy() if boxes is not None else []

        current_people = 0
        current_dogs = 0
        person_counter = 1
        dog_counter = 1

        for box in detected_objects:
            x1, y1, x2, y2, conf, cls_id = box[:6]
            cls_id = int(cls_id)

            if cls_id not in CLASS_NAMES:
                continue

            color = (0, 255, 0) if cls_id == 16 else (255, 0, 0)  # Köpek -> yeşil, insan -> mavi

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            if cls_id == 0:
                label = f"{CLASS_NAMES[cls_id].capitalize()}{person_counter}"
                cv2.putText(frame, label, (int(x1), int(y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                current_people += 1
                person_counter += 1
            elif cls_id == 16:
                label = f"{CLASS_NAMES[cls_id].capitalize()}{dog_counter}"
                cv2.putText(frame, label, (int(x1), int(y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                current_dogs += 1
                dog_counter += 1

        total_people += current_people
        total_dogs += current_dogs

        cv2.putText(frame, f"Anlık İnsan: {current_people}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Anlık Köpek: {current_dogs}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        out.write(frame)

    log_to_db(conn, filename, total_people, total_dogs, 0.0, "") # Mesafe ve durum bilgisi sıfır veya boş olarak kaydediliyor
    cap.release()
    out.release()
    conn.close()
    print(f"Video işleme tamamlandı. Çıktı dosyası: {output_video_path}")

