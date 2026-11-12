from datetime import date

from job_etl.crawl import crawl, save_raw
from job_etl.logger import setup_logging

setup_logging()
today = date.today()
save_raw(crawl(today, max_pages=2), today)