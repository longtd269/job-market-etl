from job_etl.logger import setup_logging
from job_etl.db import get_engine, run_sql_file
from job_etl.config import PROJECT_ROOT, RAW_DATA_PATH
from job_etl.transform.build import read_raw, build_tables
from job_etl.load import load_tables, prepare_tables

setup_logging()
engine = get_engine()

# create new tables
run_sql_file(engine, PROJECT_ROOT / "sql" / "02_clean.sql")
print("___End read and execute 02_clearn.sql___")

# get data from raw_job table
raw_data = read_raw(engine)

tables = build_tables(raw_data)

load_tables(prepare_tables(tables), engine)
