"""Kết nối MySQL và chạy file SQL."""
import logging
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from job_etl.config import get_database_url

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)


def run_sql_file(engine: Engine, path: Path) -> None:
    sql = Path(path).read_text(encoding="utf-8")
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
    logger.info("Đã chạy %s (%d câu lệnh)", Path(path).name, len(statements))