""" Mô tả công việc của top 10 jobs alert lên discord """
import logging
import os
import time
from datetime import date
from pathlib import Path
from typing import Callable

import pandas as pd
from curl_cffi import requests
from curl_cffi.requests.exceptions import HTTPError, RequestException
from bs4 import BeautifulSoup
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine
import re

from job_etl.crawl import HEADERS, RAW_DIR
from job_etl.transform.job_title import TECH_RULES

logger = logging.getLogger(__name__)

JD_DIR = RAW_DIR / "jd"
MAX_DETAIL_PAGES = 10
DETAIL_DELAY = 5.0
STOP_STATUS = {403, 429}

SECTIONS = {
    "description": ("mô tả công việc", "job description", "jd"),
    "requirements": ("yêu cầu ứng viên", "requirements", "candidate requirements", "yêu cầu"),
    "benefits": ("quyền lợi", "benefits", "phúc lợi"),
}

MAX_JD_CHARS = 6000
RULES = "rules"
MAX_SUMMARY_CHARS = 400

def parse_job_detail(html: str) -> dict[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, str | None] = dict.fromkeys(SECTIONS)
    for item in soup.select("div.box-job-information-detail-item"):
        title = item.select_one("h2")
        body = item.select_one("div.box-job-information-detail-item__text")
        if title is None or body is None:
            continue

        heading = title.get_text(" ", strip=True)
        clean_heading = heading.strip().lower()
        for column, prefixies in SECTIONS.items():
            if clean_heading.startswith(prefixies):
                result[column] = body.get_text("\n", strip=True)
    return result

def jd_text(detail: dict) -> str:
    names = {
        "description": "Mô tả công việc", 
        "requirements": "Yêu cầu ứng viên", 
        "benefits": "Quyền lợi"
        }
    parts = [f"## {names[col]}\n{detail[col]}" for col in names if pd.notna(detail.get(col)) and detail.get(col)]
    return "\n\n".join(parts)[:MAX_JD_CHARS]

def fetch_detail_page(session: requests.Session, url: str, timeout: int = 20) -> str | None:
    response = session.get(url)
    response.encoding = "utf-8"
    return response.text

def load_detail_pages(
    jobs: pd.DataFrame,
    cache_dir: Path,
    fetch: Callable[[str, str], str] = fetch_detail_page,
    max_pages: int = MAX_DETAIL_PAGES,
    delay: float = DETAIL_DELAY,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[int, str]:
    cache_dir = Path(cache_dir)
    pages: dict[int, str] = {}
    requests_made = from_cache = 0
    session = requests.Session(impersonate="chrome")

    for job_id, url in zip(jobs["job_id"], jobs["link_description"]):
        job_id = int(job_id)
        cache_file = cache_dir / f"{job_id}.html"
        if cache_file.exists():
            pages[job_id] = cache_file.read_text(encoding="utf-8")
            from_cache += 1
            continue
        if requests_made >= max_pages:
            logger.info("Hết ngân sách %d trang chi tiết, bỏ qua các tin còn lại", max_pages)
            break
        if requests_made > 0:
            sleep(delay)
        requests_made += 1
        try:
            html = fetch(session, url)
            logger.info("Đã tải được %s", url)
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in STOP_STATUS:
                logger.warning("TopCV trả %s ở trang chi tiết: dừng tải, không thử lại", status)
                break
            logger.warning("Không tải được %s: %s", url, exc)
            continue
        except RequestException as exc:
            logger.warning("Không tải được %s: %s", url, exc)
            continue
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(html, encoding="utf-8")
        pages[job_id] = html
    logger.info("Trang chi tiết: có %d/%d trang (%d từ cache, %d request mới)",
                len(pages), len(jobs), from_cache, requests_made)
    return pages

SKILL_RULES = [(name, pattern) for name, pattern in TECH_RULES] + [
    ("Excel", r"\bexcel\b"),
    ("Power BI", r"power\s*bi"),
    ("Tableau", r"tableau"),
    ("Looker", r"looker"),
    ("Spark", r"\bspark\b"),
    ("Airflow", r"airflow"),
    ("dbt", r"\bdbt\b"),
    ("Kafka", r"kafka"),
    ("Docker", r"docker"),
    ("Kubernetes", r"kubernetes|\bk8s\b"),
    ("Git", r"\bgit\b"),
    ("Linux", r"linux"),
    ("PostgreSQL", r"postgres"),
    ("MongoDB", r"mongo"),
    ("Azure", r"azure"),
    ("GCP", r"\bgcp\b|google cloud|bigquery"),
]

BULLET_CHARS = "•·-–+*"
MAX_LINE_CHARS = 90

def find_skills(text_jd: str) -> list[str]:
    lower = " ".join(text_jd.split()).lower()
    skills = [name for name, pattern in SKILL_RULES if re.search(pattern, lower)]
    if re.search(r"\bAI\b", text_jd) or "machine learning" in lower:
        skills.append("AI")
    return skills

def bullet_lines(section) -> list[str]:
    if section is None or pd.isna(section):
        return []
    lines = [line.strip() for line in str(section).splitlines() if line.strip()]
    bullets = [line.lstrip(BULLET_CHARS).strip() for line in lines if line[0] in BULLET_CHARS]
    return [b for b in (bullets or lines) if b]

def _short(line: str, limit: int = MAX_LINE_CHARS) -> str:
    return line if len(line) <= limit else line[: limit - 1].rstrip(" ,;.") + "…"

def summarize_rules(detail) -> str | None:
    description = bullet_lines(detail.get("description"))
    requirements = bullet_lines(detail.get("requirements"))
    benefits = [b.rstrip(" .;") for b in bullet_lines(detail.get("benefits"))]
    skills = find_skills(" ".join(description + requirements))
    experience = next((r for r in requirements if re.search(r"\d.*năm|năm.*kinh nghiệm", r.lower())), None)

    lines = []
    if description:
        lines.append(f"• Việc chính: {_short(description[0])}")
    if skills:
        lines.append(f"• Kỹ năng: {', '.join(skills)}")
    if experience:
        lines.append(f"• Kinh nghiệm: {_short(experience)}")
    if benefits:
        lines.append(f"• Quyền lợi: {_short('; '.join(benefits[:2]))}")
    return "\n".join(lines)[:MAX_SUMMARY_CHARS] or None

def read_job_details(engine: Engine, job_ids: list[int]) -> pd.DataFrame:
    if not job_ids:
        return pd.DataFrame(columns=["job_id", "description", "requirements", "benefits", "summary"])
    sql = text(
        "SELECT job_id, description, requirements, benefits, summary FROM job_details WHERE job_id IN :ids"
    ).bindparams(bindparam("ids", expanding=True))
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"ids": job_ids})    

def save_job_detail(engine: Engine, job_id: int, detail: dict) -> None:
    sql = text("""
        INSERT INTO job_details (job_id, description, requirements, benefits, fetched_at)
        VALUES (:job_id, :description, :requirements, :benefits, NOW())
        ON DUPLICATE KEY UPDATE
            description = VALUES(description), requirements = VALUES(requirements),
            benefits = VALUES(benefits), fetched_at = NOW()
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"job_id": job_id, **detail})

def save_summary(engine: Engine, job_id: int, summary: str, model: str) -> None:
    sql = text("""
        UPDATE job_details SET summary = :summary, summary_model = :model, summarized_at = NOW()
        WHERE job_id = :job_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"job_id": job_id, "summary": summary, "model": model})


def get_summaries(
    engine: Engine,
    jobs: pd.DataFrame,
    batch_date: date,
    fetch: Callable[[str, str], str] = fetch_detail_page,
    cache_root: Path = JD_DIR,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[int, str]:
    ids = [int(x) for x in jobs["job_id"]]
    known = read_job_details(engine, ids).set_index("job_id")

    missing = jobs[~jobs["job_id"].astype(int).isin(known.index)]
    pages = load_detail_pages(missing, Path(cache_root) / batch_date.isoformat(), fetch=fetch, sleep=sleep)
    for job_id, html in pages.items():
        detail = parse_job_detail(html)
        if not detail["description"]:
            logger.warning("Tin %s: không thấy mục 'Mô tả công việc' trên trang", job_id)
        save_job_detail(engine, job_id, detail)
    if pages:
        known = read_job_details(engine, ids).set_index("job_id")

    summaries = {int(i): s for i, s in known["summary"].items() if isinstance(s, str) and s}

    todo = [i for i in ids if i in known.index and i not in summaries and jd_text(known.loc[i])]
    for job_id in todo:
        summary = summarize_rules(known.loc[job_id])
        if summary:
            save_summary(engine, job_id, summary, RULES)
            summaries[job_id] = summary
    logger.info("Tóm tắt JD : %d/%d tin có tóm tắt", len(summaries), len(ids))
    return summaries