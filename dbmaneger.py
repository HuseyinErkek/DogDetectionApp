# Veritabanı bağlantısı oluştur (loglama için)
import sqlite3
from datetime import time


def init_db():
    conn = sqlite3.connect('video_processing_logs.db')
    conn.commit()
    return conn

def log_to_db(conn, filename, people, dogs, avg_distance, status):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (filename, total_people, total_dogs, confidence, status, detectionTime) VALUES (?, ?, ?, ?, ?, ?)",
                   (filename, people, dogs, avg_distance, status, time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
