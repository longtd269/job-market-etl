import argparse
import logging
from datetime import date

from job_etl.alert import build_alert_payload, filter_jobs, read_new_jobs
from job_etl.db import get_engine
from job_etl.logger import setup_logging
from job_etl.notify import post_webhook

logger = logging.getLogger("job_etl.alert")

parser = argparse.ArgumentParser(description="Gửi tin tuyển dụng mới khớp tiêu chí lên Discord.")
parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="Ngày batch, dạng YYYY-MM-DD")
args = parser.parse_args()

setup_logging()
jobs = read_new_jobs(get_engine(), args.date)
matched = filter_jobs(jobs)
logger.info("Job alert %s: %d tin mới, %d tin khớp tiêu chí", args.date, len(jobs), len(matched))

payload = build_alert_payload(matched, args.date)
if payload is None:
    logger.info("Không có tin nào khớp, không gửi")
else:
    post_webhook(payload, env_var="DISCORD_JOB_ALERT_WEBHOOK_URL")