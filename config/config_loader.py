import json
from settings import ProcessingSettings, ModelSettings


def load_processing_settings_from_json(path='config/processing_config.json') -> ProcessingSettings:
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        # JSON verilerini ProcessingSettings dataclass'ına döndürme
        return ProcessingSettings(**data)
    except FileNotFoundError:
        print(f"Error: {path} dosyası bulunamadı.")
    except json.JSONDecodeError:
        print(f"Error: {path} dosyasının formatı geçerli değil.")
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")
    return None

def load_model_settings_from_json(path='config/model_config.json') -> ModelSettings:
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        # JSON verilerini ModelSettings dataclass'ına döndürme
        return ModelSettings(**data)
    except FileNotFoundError:
        print(f"Error: {path} dosyası bulunamadı.")
    except json.JSONDecodeError:
        print(f"Error: {path} dosyasının formatı geçerli değil.")
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")
    return None
