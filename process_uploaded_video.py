import datetime
import os
import time
import threading
import traceback
import cv2
from ultralytics import YOLO
from dbmaneger import detect_object
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

    def emit_filename_initial(self, filename, session_id):
        print(f"Yeni segment başlatıldı: {filename}")
        self.socketio.emit('segment_started', {'filename': filename}, to=session_id)

    def emit_progress_update(self, progress, session_id):
        self.socketio.emit('progress', {'progress': progress}, to=session_id)

    def emit_segment_progress_update(self,segment_progress, session_id):
        self.socketio.emit('segment_progress', {
            'segment_progress': segment_progress
        }, to=session_id)

    def emit_wait_countdown(self, seconds, session_id):
        for remaining in range(seconds, 0, -1):
            self.socketio.emit('wait_timer', {'remaining_seconds': remaining}, to=session_id)
            time.sleep(1)

    def emit_error(self, message, session_id):
        self.socketio.emit('error', {'message': message}, to=session_id)

    def process_video_periodic(self, filepath: str, filename: str, session_id: str):
        if self.model is None:
            print("Model yüklenemedi, video işleme durduruldu.")
            return

        cap = None
        out = None

        try:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                error_message = f"Video açılamadı: {filepath}"
                print(error_message)
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

            #Video geneli icin olan dongu
            while frame_count < total_frames:
                print("Video İşlenmeye Başlandı")
                people_ids = set()
                dog_ids = set()
                threads = []

                current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                unique_filename = f"{base_filename}_{current_time}{ext}"
                output_path = os.path.join(output_dir, unique_filename)
                out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

                self.emit_filename_initial(unique_filename, session_id)

                segment_frame_limit = int(self.settings.work_duration * fps)
                segment_frame_counter = 0

                progress = calculate_progress(frame_count, total_frames)
                self.emit_progress_update(progress, session_id)

                #Segmentler icin olan dongu
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
                        else:
                            out.write(frame)

                        frame_count += 1
                        segment_frame_counter += 1
                        progress = calculate_progress(frame_count, total_frames)
                        self.emit_progress_update(progress, session_id)
                        segment_progress = calculate_progress(segment_frame_counter,segment_frame_limit)
                        self.emit_segment_progress_update(segment_progress, session_id)



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


                print("Segment Bitti")
                self.emit_segment_progress_update(100, session_id)

                out.release()
                out = None

                if frame_count < total_frames:
                    print(f" Bekleniyor ({self.settings.wait_duration} sn)...")
                    self.emit_wait_countdown(self.settings.wait_duration, session_id)
                    time.sleep(self.settings.wait_duration)
                    skip_frames = int(fps * self.settings.wait_duration)
                    frame_count += skip_frames
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
                else:
                    print("Video işleme tamamlandı.")
                    self.emit_progress_update(100, session_id)

            cap.release()
            cap = None

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
