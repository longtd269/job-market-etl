import argparse
import logging
from datetime import date
import sys

from job_etl.alert import MAX_EMBEDS, CRITERIA, build_alert_payload, filter_jobs, read_new_jobs
from job_etl.config import PROJECT_ROOT
from job_etl.db import get_engine, run_sql_file
from job_etl.jd import get_summaries
from job_etl.logger import setup_logging
from job_etl.notify import post_webhook

logger = logging.getLogger("job_etl.alert")

parser = argparse.ArgumentParser(description="Gửi tin tuyển dụng mới khớp tiêu chí lên Discord.")
parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="Ngày batch, dạng YYYY-MM-DD")
parser.add_argument("--no-jd", action="store_true", help="Không tải JD và không tóm tắt")
args = parser.parse_args()

setup_logging()
criteria = CRITERIA
engine = get_engine()
jobs = read_new_jobs(engine, args.date)
matched = filter_jobs(jobs, criteria)
logger.info("Job alert %s: %d tin mới, %d tin khớp tiêu chí", args.date, len(jobs), len(matched))

summaries = {}
if not args.no_jd and not matched.empty:
    run_sql_file(engine, PROJECT_ROOT / "sql" / "04_job_details.sql")
    try:
        summaries = get_summaries(engine, matched.head(MAX_EMBEDS), args.date)
    except Exception:
        logger.exception("Lỗi khi lấy tóm tắt JD: vẫn gửi alert không kèm tóm tắt")

payload = build_alert_payload(matched, args.date, criteria, summaries)
if payload is None:
    logger.info("Không có tin nào khớp, không gửi")
else:
    post_webhook(payload, env_var="DISCORD_JOB_ALERT_WEBHOOK_URL")