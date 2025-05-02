import os
import time
import threading
import traceback

import cv2
from ultralytics import YOLO
from dbmaneger import detect_object
from settings import ProcessingSettings, ModelSettings


class VideoProcessor:
    def __init__(self, settings: ProcessingSettings, model_settings: ModelSettings):
        self.settings = settings
        self.model_settings = model_settings
        try:
            self.model = YOLO(self.model_settings.model_path)
        except Exception as e:
            print(f" Model yüklenirken hata oluştu: {e}")
            traceback.print_exc()
            raise

    def process_video_periodic(self, filepath: str, filename: str):
        try:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                print(f" Video açılamadı: {filepath}")
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
                threads = []

                while time.time() - segment_start_time < self.settings.work_duration and frame_count < total_frames:
                    try:
                        ret, frame = cap.read()
                        if not ret:
                            print("⚠️ Kare okunamadı.")
                            break

                        if frame_count % (self.settings.skip_rate + 1) == 0:
                            try:
                                results = self.model.track(
                                    source=frame,
                                    stream=True,  # NOTE: stream=True sadece video/URL için uygundur
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
                                        try:
                                            object_type = None
                                            if int(cls) == 0 and obj_id not in people_ids:
                                                object_type = "person"
                                                people_ids.add(int(obj_id))
                                            elif int(cls) == 16 and obj_id not in dog_ids:
                                                object_type = "dog"
                                                dog_ids.add(int(obj_id))

                                            if object_type:
                                                thread = threading.Thread(target=detect_object, args=(obj_id, object_type, filename))
                                                thread.start()
                                                threads.append(thread)
                                        except Exception as e:
                                            print(f" Nesne işlenirken hata oluştu: {e}")
                                            traceback.print_exc()
                            except Exception as e:
                                print(f" YOLO model işlemesi sırasında hata: {e}")
                                traceback.print_exc()

                        frame_count += 1
                    except Exception as e:
                        print(f" Kare işlenirken hata oluştu: {e}")
                        traceback.print_exc()

                # Thread'lerin tamamlanmasını bekle
                for t in threads:
                    try:
                        t.join()
                    except Exception as e:
                        print(f" Thread sonlandırılırken hata: {e}")
                        traceback.print_exc()

                if frame_count < total_frames:
                    print(f"⏳ Bekleniyor ({self.settings.wait_duration} sn)...")
                    time.sleep(self.settings.wait_duration)
                    segment_number += 1
                else:
                    print("✅ Video işleme tamamlandı.")

            cap.release()

        except Exception as e:
            print(f"🚨 Genel hata: {e}")
            traceback.print_exc()
