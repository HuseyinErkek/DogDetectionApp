import os
import sqlite3
import time
from datetime import datetime

import cv2
from ultralytics import YOLO
from dbmaneger import init_db, log_to_db, log_dog_detections_to_db
from settings import ProcessingSettings, ModelSettings


class VideoProcessor:
    def __init__(self, settings: ProcessingSettings, model_settings: ModelSettings, conn: sqlite3.Connection):
        self.settings = settings
        self.model_settings = model_settings
        self.conn = init_db()
        self.model = YOLO(self.model_settings.model_path)  # Modeli yolundan yükle

    def process_video_periodic(self, filepath: str, filename: str):
        cap = cv2.VideoCapture(filepath)

        if not cap.isOpened():
            print(f"Video açılamadı: {filepath}")
            return

        output_dir = os.path.join(os.path.dirname(filepath), 'processed_videos_periodic')
        os.makedirs(output_dir, exist_ok=True)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        segment_number = 1

        while frame_count < total_frames:
            segment_start_time = time.time()
            people_ids = set()
            dog_ids = set()
            dog_detections = []  # (Dog id, detection_time) listesi
            person_detections = [] #(Person id, detection_time) listesi

            while time.time() - segment_start_time < self.settings.work_duration and frame_count < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % (self.settings.skip_rate + 1) == 0:
                    results = self.model.track(
                        source=frame,
                        stream=True,
                        conf=0.5,
                        iou=0.5,
                        persist=True,
                        save=True,
                        project=output_dir,
                        name="takip_sonucu",
                        tracker="config/deepsort.yaml"
                    )

                    if results and results[0].boxes.id is not None:
                        ids = results[0].boxes.id.cpu().tolist()
                        classes = results[0].boxes.cls.cpu().tolist()

                        for obj_id, cls in zip(ids, classes):
                            detection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            if int(cls) == 0:
                                people_ids.add(int(obj_id))
                                log_dog_detections_to_db(self.conn,obj_id,detection_time)
                                person_detections.append((int(obj_id), detection_time))
                            elif int(cls) == 16:
                                dog_ids.add(int(obj_id))
                                dog_detections.append((int(obj_id), detection_time))

                frame_count += 1

            # Veritabanına köpek tespitlerini kaydet
            log_dog_detections_to_db(self.conn, filename, dog_detections)

            # Segment istatistiklerini kaydet
            log_to_db(
                self.conn,
                filename,
                detection_time,
                len(people_ids),
                len(dog_ids),
            )

            # Bekleme süresi
            if frame_count < total_frames:
                print(f"⏳ Bekleniyor ({self.settings.wait_duration} sn)...")
                time.sleep(self.settings.wait_duration)
                segment_number += 1
            else:
                print("🎬 Video işleme tamamlandı.")

        cap.release()
        self.conn.close()
