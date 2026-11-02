"""Đọc cấu hình từ file .env để dùng chung cho toàn project."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

RAW_DATA_PATH = PROJECT_ROOT / os.getenv("RAW_DATA_PATH", "data/raw/jobs.csv")


def get_database_url() -> str:
    """Chuỗi kết nối MySQL cho SQLAlchemy (driver PyMySQL, utf8mb4 để lưu tiếng Việt)."""
    user = os.getenv("MYSQL_USER", "job_etl")
    password = os.getenv("MYSQL_PASSWORD", "")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DATABASE", "jobs")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
