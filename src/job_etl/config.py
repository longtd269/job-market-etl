"""Đọc cấu hình từ file .env để dùng chung cho toàn project."""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

RAW_DATA_PATH = PROJECT_ROOT / os.getenv("RAW_DATA_PATH", "data/raw/jobs.csv")


def get_database_url() -> URL:
    """Chuỗi kết nối MySQL cho SQLAlchemy (driver PyMySQL, utf8mb4 để lưu tiếng Việt)."""
    return URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER", "job_etl"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "jobs"),
        query={"charset": "utf8mb4"},
    )
