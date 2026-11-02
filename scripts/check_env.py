"""Kiểm tra nhanh môi trường: thư viện, file dữ liệu, kết nối PostgreSQL.

Chạy: python scripts/check_env.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from sqlalchemy import create_engine, text

from job_etl.config import RAW_DATA_PATH, get_database_url


def main() -> int:
    print(f"Python  : {sys.version.split()[0]}")
    print(f"pandas  : {pd.__version__}")

    df = pd.read_csv(RAW_DATA_PATH)
    print(f"Dữ liệu : {RAW_DATA_PATH.name} -> {df.shape[0]} dòng, cột = {list(df.columns)}")

    try:
        engine = create_engine(get_database_url())
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
        print(f"Postgres: OK ({version.split(',')[0]})")
    except Exception as exc:  # noqa: BLE001
        print(f"Postgres: CHƯA KẾT NỐI ĐƯỢC -> {exc.__class__.__name__}: {exc}".splitlines()[0])
        print("          Hãy chạy `docker compose up -d` và kiểm tra file .env")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
