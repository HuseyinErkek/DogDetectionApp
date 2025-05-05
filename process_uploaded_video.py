import datetime
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

            output_dir = os.path.join(os.getcwd(), 'processed_videos')
            os.makedirs(output_dir, exist_ok=True)

            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            base_filename, ext = os.path.splitext(filename)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_count = 0

            while frame_count < total_frames:
                print("Video İşlenmeye Başlandı")
                segment_start_time = time.time()
                people_ids = set()
                dog_ids = set()
                threads = []

                current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                unique_filename = f"{base_filename}_{current_time}{ext}"
                output_path = os.path.join(output_dir, unique_filename)
                out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

                # Kare sayısı bazında süre kontrolü
                segment_frame_limit = int(self.settings.work_duration * fps)
                segment_frame_counter = 0

                while segment_frame_counter < segment_frame_limit and frame_count < total_frames:
                    try:
                        ret, frame = cap.read()
                        if not ret:
                            print("️Kare okunamadı.")
                            break

                        if frame_count % (self.settings.skip_rate + 1) == 0:
                            try:
                                results = self.model.track(
                                    verbose=False,
                                    source=frame,
                                    stream=False,
                                    conf=0.5,
                                    iou=0.5,
                                    persist=True,
                                    tracker="botsort.yaml"
                                )

                                for result in results:
                                    annotated_frame = result.plot()
                                    out.write(annotated_frame)

                                    if result.boxes.id is not None:
                                        ids = result.boxes.id.cpu().tolist()
                                        classes = result.boxes.cls.cpu().tolist()

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
                                                    thread = threading.Thread(
                                                        target=detect_object,
                                                        args=(obj_id, object_type, filename)
                                                    )
                                                    thread.start()
                                                    threads.append(thread)
                                            except Exception as e:
                                                print(f" Nesne işlenirken hata oluştu: {e}")
                                                traceback.print_exc()
                            except Exception as e:
                                print(f" YOLO model işlemesi sırasında hata: {e}")
                                traceback.print_exc()
                        else:
                            out.write(frame)

                        frame_count += 1
                        segment_frame_counter += 1
                    except Exception as e:
                        print(f" Kare işlenirken hata oluştu: {e}")
                        traceback.print_exc()

                for t in threads:
                    try:
                        t.join()
                    except Exception as e:
                        print(f"️ Thread sonlandırılırken hata: {e}")
                        traceback.print_exc()

                out.release()

                # 2 dakikalık video içeriğini atla
                if frame_count < total_frames:
                    print(f"Video({self.settings.wait_duration})")
                    print(f" Bekleniyor ({self.settings.wait_duration} sn)...")

                    skip_frames = int(fps * self.settings.wait_duration)
                    frame_count += skip_frames
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)

                    time.sleep(self.settings.wait_duration)
                else:
                    print(" Video işleme tamamlandı.")

            cap.release()

        except Exception as e:
            print(f" Genel hata: {e}")
            traceback.print_exc()
