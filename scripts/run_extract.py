from job_etl.logger import setup_logging
from job_etl.db import get_engine, run_sql_file
from job_etl.config import PROJECT_ROOT, RAW_DATA_PATH
from job_etl.extract import load_to_db, read_raw_csv

setup_logging()
engine = get_engine()

run_sql_file(engine, PROJECT_ROOT / "sql" / "01_raw.sql")
print("___End read and execute 01_raw.sql___")

raw = read_raw_csv(RAW_DATA_PATH)
print("___End read csv___")

load_to_db(raw, engine)
print("___End load to db___")
