"""Chạy tất cả các hàm transform"""
import logging

import pandas as pd
from sqlalchemy.engine import Engine

from job_etl.transform.salary import transform_salary
from job_etl.transform.address import transform_address

logger = logging.getLogger(__name__)


def read_raw(engine: Engine) -> pd.DataFrame:
    """Đọc bảng raw_jobs"""
    df = pd.read_sql("SELECT * FROM raw_jobs ORDER BY id", engine)
    logger.info("Đọc raw_jobs: %d dòng", len(df))
    return df

def build_tables(data_raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    jobs = transform_salary(data_raw)
    print("___End transform salary__")
    jobs, job_locations = transform_address(jobs)
    print("___End transform address__")
    return {"jobs": jobs, "job_locations": job_locations}