from job_etl.logger import setup_logging
from job_etl.db import get_engine, run_sql_file
from job_etl.config import PROJECT_ROOT, RAW_DATA_PATH
from job_etl.transform.build import read_raw, build_tables

setup_logging()
engine = get_engine()

raw_data = read_raw(engine)

tables = build_tables(raw_data)

out_dir = PROJECT_ROOT / "data" / "processed"

for name, table in tables.items():
    name = f"{name}_preview.csv"
    out_path = out_dir / name
    table.to_csv(out_path, index=False)
    print(f"Đã ghi {len(table)} dòng ra file {name}")