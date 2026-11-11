"""Chạy tất cả các hàm transform"""
import logging

import pandas as pd
from sqlalchemy.engine import Engine

from job_etl.transform.salary import transform_salary
from job_etl.transform.address import transform_address
from job_etl.transform.job_title import transform_job_title, transform_technologies
from job_etl.transform.link import transform_links

logger = logging.getLogger(__name__)


def read_raw(engine: Engine) -> pd.DataFrame:
    """Đọc bảng raw_jobs"""
    df = pd.read_sql("SELECT * FROM raw_jobs ORDER BY row_id", engine)
    logger.info("Đọc raw_jobs: %d dòng", len(df))
    return df

def build_tables(data_raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    jobs = transform_links(data_raw)
    jobs = transform_salary(jobs)
    print("___End transform salary__")
    jobs = transform_job_title(jobs)
    print("___End transform job title__")
    jobs, job_locations = transform_address(jobs)
    print("___End transform address__")
    job_technologies = transform_technologies(jobs)
    print("___End extract technologies__")


    return {"jobs": jobs, "job_locations": job_locations, "job_technologies": job_technologies}