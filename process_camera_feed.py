from ultralytics import YOLO
import sqlite3
import cv2

model_path = 'model/yolov8m_epochs50.pt'  # Yolov8 model yolu
camera_threads = {}
def process_camera_feed(camera_id, camera_url):
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_id}")
        return


    model = YOLO(model_path)

    while camera_id in camera_threads and camera_threads[camera_id]['active']:
        ret, frame = cap.read()
        if not ret:
            print(f"Error: Could not read frame from camera {camera_id}")
            break

        # Detect dogs in the frame
        detections = model.detect(frame)

        # Save detections to database
        if detections:
            conn = sqlite3.connect('dogdetection.db')
            cursor = conn.cursor()
            for detection in detections:
                confidence, x, y, width, height = detection
                cursor.execute('''
                INSERT INTO detections (camera_id, confidence, x, y, source_type)
                VALUES (?, ?, ?, ?, ?)
                ''', (camera_id, confidence, x, y, 'camera'))
            conn.commit()
            conn.close()

        # Sleep to reduce CPU usage
        import time
        time.sleep(0.1)

    cap.release()