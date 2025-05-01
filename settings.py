from dataclasses import dataclass

@dataclass
class ProcessingSettings:
    skip_rate: int = 3
    work_duration: int = 60
    wait_duration: int = 120

@dataclass
class ModelSettings:
    model_path: str = 'model/yolov8m_epochs50.pt'
