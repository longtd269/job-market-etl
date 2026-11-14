"""Chạy tất cả các hàm extract, transform, load"""
import logging
import time
from contextlib import contextmanager
from pathlib import Path
from datetime import date
import argparse

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.engine import Engine

from job_etl.config import PROJECT_ROOT, RAW_DATA_PATH
from job_etl.db import get_engine, run_sql_file
from job_etl.extract import load_to_db, read_raw_csv
from job_etl.transform.build import build_tables, read_raw
from job_etl.load import load_tables, prepare_tables
from job_etl.crawl import crawl, save_raw, read_saved_pages
from job_etl.notify import build_message, send_discord

logger = logging.getLogger(__name__)
SQL_DIR = PROJECT_ROOT / "sql"

EXIT_OK = 0
EXIT_ERROR = 1

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

def run_pipeline(file_path: Path, engine: Engine, batch_date: date, 
                 do_crawl: bool = False, html_dir: Path | None = None) -> dict[str, int]:
    with step("connect DB"):
        wait_for_db(engine)

    if do_crawl:
        with step("Crawl"):
            file_path = save_raw(crawl(batch_date), batch_date)
    elif html_dir is not None:
        with step("Read HTML đã lưu"):
            file_path = save_raw(read_saved_pages(html_dir, batch_date), batch_date)    
    
    with step("Extract"):
        run_sql_file(engine, SQL_DIR / "01_raw.sql")
        raw = read_raw_csv(file_path)
        load_to_db(raw, engine)

    with step("Transform"):
        raw_data = read_raw(engine)
        tables = build_tables(raw_data)

    with step("Load"):
        run_sql_file(engine, SQL_DIR / "02_clean.sql")
        counts = load_tables(prepare_tables(tables), engine, batch_date)

    return counts

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chạy pipeline")
    parser.add_argument("--csv", type=Path, default=RAW_DATA_PATH, help="Đường dẫn file CSV gốc")
    parser.add_argument(
        "--date", type=date.fromisoformat, default=date.today(),
        help="Ngày của dữ liệu, dạng YYYY-MM-DD (mặc định: hôm nay)",
    )
    parser.add_argument("--no-notify", action="store_true", help="Không gửi thông báo Discord")

    source = parser.add_mutually_exclusive_group()
    source.add_argument("--crawl", action="store_true", help="Crawl TopCV trước, bỏ qua --csv")
    source.add_argument("--html-dir", type=Path, help="Thư mục chứa trang TopCV đã lưu bằng trình duyệt")
    args = parser.parse_args(argv)

    logger.info("===== Pipeline bắt đầu: %s, ngày %s =====", args.csv, args.date)
    start = time.perf_counter()
    counts, code = None, None
    try:
        counts = run_pipeline(args.csv, get_engine(), args.date, do_crawl = args.crawl, html_dir = args.html_dir)
        code = EXIT_OK
    except Exception as e:
        code = EXIT_ERROR

    seconds = time.perf_counter() - start
    if code == EXIT_OK:
        logger.info("===== Pipeline thành công sau %.1fs: %s =====", seconds, counts)
    else:
        logger.error("===== Pipeline thất bại sau %.1fs =====", seconds)

    if not args.no_notify:
        send_discord(build_message(code, args.date, seconds, counts=counts))

    return code    