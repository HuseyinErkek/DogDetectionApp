import datetime
import os
import time
import threading
import traceback
import cv2
from ultralytics import YOLO
from dbmaneger import detect_object  # Gerçek dosya yolunuza göre düzenleyin
from settings import ProcessingSettings, ModelSettings
from flask_socketio import SocketIO


def calculate_progress(frame_count, total_frames):
    if total_frames == 0:
        return 0
    return (frame_count / total_frames) * 100


class VideoProcessor:
    def __init__(self, settings: ProcessingSettings, model_settings: ModelSettings, socketio: SocketIO):
        self.socketio = socketio
        self.settings = settings
        self.model_settings = model_settings
        self.model = self._load_model()

    def _load_model(self):
        try:
            model = YOLO(self.model_settings.model_path)
            return model
        except Exception as e:
            error_message = f"Model yüklenirken hata oluştu: {e}"
            print(error_message)
            traceback.print_exc()
            self.socketio.emit('error', {'message': error_message})
            return None

    def emit_progress(self, progress, filename):
        print(f"İşleniyor: %{progress:.2f} - {filename}")
        data = {'filename': filename, 'progress': progress}
        self.socketio.emit('progress', data)

    def process_video_periodic(self, filepath: str, filename: str):
        global unique_filename
        if self.model is None:
            print("Model yüklenemedi, video işleme durduruldu.")
            self.socketio.emit('error', {'message': 'Model yüklenemedi'})
            return

        cap = None
        out = None

        try:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                error_message = f"Video açılamadı: {filepath}"
                print(error_message)
                self.socketio.emit('error', {'message': error_message})
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
                people_ids = set()
                dog_ids = set()
                threads = []

                current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                unique_filename = f"{base_filename}_{current_time}{ext}"
                output_path = os.path.join(output_dir, unique_filename)
                out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

                segment_frame_limit = int(self.settings.work_duration * fps)
                segment_frame_counter = 0

                progress = calculate_progress(frame_count, total_frames)
                self.emit_progress(progress, filename)

                while segment_frame_counter < segment_frame_limit and frame_count < total_frames:
                    try:
                        ret, frame = cap.read()
                        if not ret:
                            print("Kare okunamadı. Segment sonlandırılıyor.")
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
                                    tracker="botsort.yaml",
                                )

                                if results:
                                    for result in results:
                                        annotated_frame = result.plot()
                                        out.write(annotated_frame)

                                        if result.boxes.id is not None:
                                            ids = result.boxes.id.cpu().tolist()
                                            classes = result.boxes.cls.cpu().tolist()
                                            for obj_id, cls in zip(ids, classes):
                                                object_type = None
                                                if int(cls) == 0 and obj_id not in people_ids:
                                                    object_type = "person"
                                                    people_ids.add(obj_id)
                                                elif int(cls) == 16 and obj_id not in dog_ids:
                                                    object_type = "dog"
                                                    dog_ids.add(obj_id)

                                                if object_type:
                                                    thread = threading.Thread(
                                                        target=detect_object,
                                                        args=(obj_id, object_type, filename),
                                                    )
                                                    thread.start()
                                                    threads.append(thread)
                            except Exception as e:
                                error_message = f"YOLO model hatası: {e}"
                                print(error_message)
                                traceback.print_exc()
                                self.socketio.emit('error', {'message': error_message})
                        else:
                            out.write(frame)

                        frame_count += 1
                        segment_frame_counter += 1
                        progress = calculate_progress(frame_count, total_frames)
                        self.emit_progress(progress, unique_filename)

                    except Exception as e:
                        error_message = f"Kare işleme hatası: {e}"
                        print(error_message)
                        traceback.print_exc()
                        break

                for t in threads:
                    try:
                        t.join()
                    except Exception as e:
                        error_message = f"Thread hatası: {e}"
                        print(error_message)
                        traceback.print_exc()

                out.release()
                out = None

                if frame_count < total_frames:
                    print(f" Bekleniyor ({self.settings.wait_duration} sn)...")
                    time.sleep(self.settings.wait_duration)
                    skip_frames = int(fps * self.settings.wait_duration)
                    frame_count += skip_frames
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
                else:
                    print("Video işleme tamamlandı.")
                    progress = 100
                    self.emit_progress(progress, unique_filename)

            cap.release()
            cap = None
            self.emit_progress(100, unique_filename)

        except Exception as e:
            error_message = f"Video işleme genel hata: {e}"
            print(error_message)
            traceback.print_exc()
        finally:
            try:
                if cap is not None:
                    cap.release()
                if out is not None:
                    out.release()
            except Exception as e:
                error_message = f"Video kaynakları serbest bırakılırken hata: {e}"
                print(error_message)
                traceback.print_exc()
