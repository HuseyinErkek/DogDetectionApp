import cv2
import sqlite3
from ultralytics import YOLO
import time

model_path = 'model/yolov8m_epochs50.pt'  # Yolov8 model yolu


def process_uploaded_video(filepath, filename):
    # Video dosyasını OpenCV ile açıyoruz
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        print(f"Error: Could not open video file {filename}")
        return

    # Köpek tespiti için modelimizi başlatıyoruz (bu kısım daha önce tanımlanmıştı)
    model = YOLO(model_path)

    # Video akışındaki her kareyi işlemeye başlıyoruz
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Video bitince döngüyü sonlandır

        # Köpek tespiti yapıyoruz
        detections = model.detect(frame)

        # Eğer tespitler varsa, veritabanına kaydediyoruz
        if detections:
            conn = sqlite3.connect('dogdetection.db')  # Veritabanı dosyasını doğru şekilde ayarlayın
            cursor = conn.cursor()

            for detection in detections:
                confidence, x, y, width, height = detection
                cursor.execute('''
                INSERT INTO detections (camera_id, confidence, x, y, source_type, source_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (None, confidence, x, y, 'video', filename))  # Kamera ID'si yoksa None, video ismi kaydedilir

            conn.commit()
            conn.close()



        time.sleep(0.1)
    # Video işleme tamamlandıktan sonra kaynağı serbest bırakıyoruz
    cap.release()
    cv2.destroyAllWindows()
    print(f"Video processing completed for {filename}")
