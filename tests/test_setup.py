"""Test kiểm tra môi trường đã sẵn sàng (sẽ thay bằng test thật ở các bước sau)."""
import pandas as pd

from job_etl.config import RAW_DATA_PATH, get_database_url

EXPECTED_COLUMNS = [
    "created_date", "job_title", "company", "salary",
    "address", "time", "link_description",
]


def test_raw_data_has_expected_columns():
    df = pd.read_csv(RAW_DATA_PATH)
    assert list(df.columns) == EXPECTED_COLUMNS
    assert len(df) > 0


def test_database_url_uses_mysql_driver():
    url = get_database_url()
    assert url.startswith("mysql+pymysql://")
    assert url.endswith("charset=utf8mb4")
