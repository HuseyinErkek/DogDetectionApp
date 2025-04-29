import sqlite3
import cv2
import numpy as np
from ultralytics import YOLO
import os
from dbmaneger import init_db,log_to_db

# YOLOv8 model yolu
MODEL_PATH = 'model/yolov8m_epochs50.pt'

# Nesne sınıfları (COCO dataset class IDs)
CLASS_NAMES = {
    0: 'person',
    16: 'dog'
}

# Odak uzunluğu (kamera kalibrasyonuyla alınmalı)
FOCAL_LENGTH = 192  # px
REAL_DOG_WIDTH = 0.8  # metre

def process_uploaded_video(filepath, filename):
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        raise ValueError("Video dosyası açılamadı. Lütfen yolu kontrol edin.")

    # FPS kontrolü
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 25  # varsayılan fps atanabilir

    model = YOLO(MODEL_PATH)
    conn = init_db()

    output_dir = os.path.join(os.path.dirname(filepath), 'processed_videos')
    os.makedirs(output_dir, exist_ok=True)
    output_video_path = os.path.join(output_dir, filename)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    total_people, total_dogs = 0, 0
    dog_coordinates, box_sizes = [], []
    distances = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        boxes = results[0].boxes
        detected_objects = boxes.data.cpu().numpy() if boxes is not None else []

        for box in detected_objects:
            x1, y1, x2, y2, conf, cls_id = box[:6]
            cls_id = int(cls_id)

            if cls_id not in CLASS_NAMES:
                continue

            label = CLASS_NAMES[cls_id].capitalize()
            color = (0, 255, 0) if cls_id == 16 else (255, 0, 0)  # Köpek -> yeşil, insan -> mavi vb.

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.putText(frame, label, (int(x1), int(y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            if cls_id == 0:
                total_people += 1
            elif cls_id == 16:
                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                width, height = x2 - x1, y2 - y1
                dog_coordinates.append((mid_x, mid_y))
                box_sizes.append((width, height))

        if dog_coordinates:
            avg_box_size = np.mean([max(w, h) for w, h in box_sizes])
            threshold_distance = avg_box_size * 0.8

            is_pack = any(
                np.linalg.norm(np.array(dog_coordinates[i]) - np.array(dog_coordinates[j])) < threshold_distance
                for i in range(len(dog_coordinates))
                for j in range(i + 1, len(dog_coordinates))
            )

            status_text = "Dogs are in pack." if is_pack else "Dog is alone."
            cv2.putText(frame, status_text, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            for i in range(len(dog_coordinates)):
                for j in range(i + 1, len(dog_coordinates)):
                    d = np.linalg.norm(np.array(dog_coordinates[i]) - np.array(dog_coordinates[j]))
                    distances.append(d)

        if distances:
            avg_pixel_distance = np.mean(distances)
            real_distance = (REAL_DOG_WIDTH * FOCAL_LENGTH) / avg_pixel_distance
            cv2.putText(frame, f"Avg. Distance: {real_distance:.2f} m", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            real_distance = 0.0
            status_text = "Dog is alone."

        cv2.putText(frame, f"Total People: {total_people}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Total Dogs: {len(dog_coordinates)}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        out.write(frame)

    log_to_db(conn, filename, total_people, len(dog_coordinates), real_distance, status_text)
    cap.release()
    out.release()
    conn.close()
    print(f"Video işleme tamamlandı. Çıkış dosyası: {output_video_path}")
