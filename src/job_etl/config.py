"""Đọc cấu hình từ file .env để dùng chung cho toàn project."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

RAW_DATA_PATH = PROJECT_ROOT / os.getenv("RAW_DATA_PATH", "data/raw/jobs.csv")


def get_database_url() -> str:
    """Chuỗi kết nối PostgreSQL cho SQLAlchemy."""
    user = os.getenv("POSTGRES_USER", "job_etl")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "jobs")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
