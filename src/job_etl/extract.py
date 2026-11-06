import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "created_date",
    "job_title",
    "company",
    "salary",
    "address",
    "time",
    "link_description",
]

def validate_colums(df: pd.DataFrame) -> None:
    missing = []
    for column in EXPECTED_COLUMNS:
        if column not in df.columns:
            missing.append(column)
    if missing:
        raise Exception(f"CSV thiếu cột: {', '.join(missing)}") 


    extra = []
    for column in df.columns:
        if column not in EXPECTED_COLUMNS:
            extra.append(column)
    if extra:
        logger.warning(f"CSV có cột lạ: {', '.join(extra)}")


def read_raw_csv(path: Path) -> pd.DataFrame:
    path = Path(path)
    df = pd.read_csv(path, dtype=str)
    logger.info("Đọc %s: %d dòng, %d cột", path.name, len(df), len(df.columns))

    validate_colums(df)

    df = df[EXPECTED_COLUMNS]
    df.insert(0, "id", range(1, len(df) + 1))
    df["source_file"] = path.name

    return df     

def load_to_db(df: pd.DataFrame, engine: Engine) -> int:
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM raw_jobs'))
        df.to_sql("raw_jobs", conn, if_exists="append", index=False, chunksize=500)
        count = conn.execute(text("SELECT COUNT(*) FROM raw_jobs")).scalar_one()

    logger.info("Đã ghi %d dòng vào raw_jobs", count)
    return count
