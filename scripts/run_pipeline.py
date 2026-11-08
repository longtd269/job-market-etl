from job_etl.logger import setup_logging
from job_etl.pipeline import run_pipeline
from job_etl.db import get_engine
from job_etl.config import PROJECT_ROOT, RAW_DATA_PATH

setup_logging()
run_pipeline(RAW_DATA_PATH, get_engine())
