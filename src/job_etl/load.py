import logging

import pandas as pd
from datetime import date
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
import sys


logger = logging.getLogger(__name__)

JOB_DATA_COLUMNS = [
    "created_date", "job_title", "job_group", "job_level", "company",
    "salary", "min_salary", "max_salary", "salary_unit", "address", "link_description",
]

TABLE_COLUMNS = {
    "jobs": ["row_id", *JOB_DATA_COLUMNS],
    "job_locations": ["row_id", "location_order", "city", "district"],
    "job_technologies": ["row_id", "technology"],
}

CHILD_TABLES = ["job_locations", "job_technologies"]

_cols = ", ".join(JOB_DATA_COLUMNS)
_select_cols = ", ".join(f"b.{c}" for c in JOB_DATA_COLUMNS)
_update_cols = ",\n    ".join(f"{c} = b.{c}" for c in JOB_DATA_COLUMNS if c != "link_description")

UPSERT_JOBS_SQL = f"""
INSERT INTO jobs ({_cols}, first_seen, last_seen)
SELECT {_select_cols}, :batch_date, :batch_date
FROM load_jobs_batch AS b
ON DUPLICATE KEY UPDATE
    {_update_cols},
    first_seen = LEAST(jobs.first_seen, :batch_date),
    last_seen = GREATEST(jobs.last_seen, :batch_date)
"""

JOB_ID_MAPPING_SQL = """
SELECT b.row_id, j.job_id
FROM load_jobs_batch AS b
JOIN jobs AS j ON j.link_description = b.link_description
"""

def prepare_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    prepared = {}
    for name, columns in TABLE_COLUMNS.items():
        df = tables[name]
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise KeyError(f"Bảng {name} thiếu cột {missing}. Đang có: {list(df.columns)}")
        prepared[name] = df[columns]

    return prepared

def attach_job_id(child: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    merged = child.merge(mapping, on="row_id", how="left", validate="many_to_one")
    if merged["job_id"].isna().any():
        missing = merged.loc[merged["job_id"].isna(), "row_id"].unique().tolist()
        raise ValueError(f"Không tìm thấy job_id cho row_id {missing}")
    columns = ["job_id"] + [c for c in child.columns if c != "row_id"]
    return merged[columns].astype({"job_id": int})

def _count(conn: Connection, sql: str, **params) -> int:
    return conn.execute(text(sql), params).scalar_one()

def load_tables(tables: dict[str, pd.DataFrame], engine: Engine, batch_date: date = date.today()) -> dict[str, int]:
    with engine.begin() as conn:
        jobs_before = _count(conn, "SELECT COUNT(*) FROM jobs")

        conn.execute(text("DELETE FROM load_jobs_batch"))
        tables["jobs"].to_sql("load_jobs_batch", conn, if_exists="append", index=False, chunksize=500)
        conn.execute(text(UPSERT_JOBS_SQL), {"batch_date": batch_date})
        mapping = pd.read_sql(text(JOB_ID_MAPPING_SQL), conn)

        for name in CHILD_TABLES:
            conn.execute(text(f"""
                DELETE c FROM {name} AS c
                JOIN jobs AS j ON j.job_id = c.job_id
                JOIN load_jobs_batch AS b ON b.link_description = j.link_description
            """))
            attach_job_id(tables[name], mapping).to_sql(
                name, conn, if_exists="append", index=False, chunksize=500
            )

        jobs_after = _count(conn, "SELECT COUNT(*) FROM jobs")
        counts = {
            "batch": len(tables["jobs"]),
            "new_jobs": jobs_after - jobs_before,
            "updated_jobs": len(tables["jobs"]) - (jobs_after - jobs_before),
            "total_jobs": jobs_after,
            "active_jobs": _count(conn, "SELECT COUNT(*) FROM jobs WHERE last_seen = :d", d=batch_date),
        } 
        logger.info("Load xong batch %s: %s", batch_date, counts)
        return counts