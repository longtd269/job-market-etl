"""Chạy tất cả các hàm extract, transform, load"""
import logging
import time
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.engine import Engine

from job_etl.config import PROJECT_ROOT, RAW_DATA_PATH
from job_etl.db import get_engine, run_sql_file
from job_etl.extract import load_to_db, read_raw_csv
from job_etl.transform.build import build_tables, read_raw
from job_etl.load import load_tables, prepare_tables


logger = logging.getLogger(__name__)
SQL_DIR = PROJECT_ROOT / "sql"

EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_DATA_QUALITY = 2
EXIT_DATABASE = 3

@contextmanager
def step(name: str):
    logger.info("Bắt đầu bước %s", name)
    start = time.perf_counter()
    try:
        yield
    except Exception:
        logger.error("Bước %s lỗi sau %.2fs", name, time.perf_counter() - start)
        raise
    logger.info("Xong bước %s (%.2fs)", name, time.perf_counter() - start)

def wait_for_db(engine: Engine, retries: int = 3, delay: float = 5) -> None:
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError as exc:
            logger.warning("Chưa kết nối được MySQL (lần %d/%d): %s", attempt, retries, exc.orig)
            if attempt == retries:
                raise
            time.sleep(delay)  

def run_pipeline(file_path: Path, engine: Engine) -> dict[str, int]:
    with step("connect DB"):
        wait_for_db(engine)
    
    with step("Extract"):
        run_sql_file(engine, SQL_DIR / "01_raw.sql")
        raw = read_raw_csv(file_path)
        load_to_db(raw, engine)

    with step("Transform"):
        raw_data = read_raw(engine)
        tables = build_tables(raw_data)

    with step("Load"):
        run_sql_file(engine, SQL_DIR / "02_clean.sql")
        counts = load_tables(prepare_tables(tables), engine)

    return counts 