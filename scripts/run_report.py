from job_etl.logger import setup_logging
from job_etl.pipeline import run_pipeline
from job_etl.db import get_engine, run_sql_file
from job_etl.config import PROJECT_ROOT, RAW_DATA_PATH
from job_etl.report import build_report

setup_logging()
engine = get_engine()
run_sql_file(engine, PROJECT_ROOT / "sql" / "03_mart.sql")
build_report(engine)
