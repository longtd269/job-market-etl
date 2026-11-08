import logging

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
import sys


logger = logging.getLogger(__name__)

TABLE_COLUMNS = {
    "jobs": [
        "id", "created_date", "job_title", "job_group", "job_level", "company",
        "salary", "min_salary", "max_salary", "salary_unit", "address", "link_description",
    ],
    "job_locations": ["job_id", "location_order", "city", "district"],
    "job_technologies": ["job_id", "technology"],
}

def prepare_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    prepared = {}
    for name, columns in TABLE_COLUMNS.items():
        df = tables[name]
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise KeyError(f"Bảng {name} thiếu cột {missing}. Đang có: {list(df.columns)}")
        prepared[name] = df[columns]

    return prepared


def load_tables(tables: dict[str, pd.DataFrame], engine: Engine) -> dict[str, int]:
    names = list(TABLE_COLUMNS)
    with engine.begin() as conn:
        for name in reversed(names):
            # delete before load new data
            conn.execute(text(f"DELETE FROM {name}"))

        for name in names:    
            # load to db    
            tables[name].to_sql(name, conn, if_exists="append", index=False, chunksize=500)
            
        counts = {
            name: conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
            for name in names
        }
    logger.info("Load xong: %s", counts)  
    return counts