import logging
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from job_etl.config import PROJECT_ROOT
from job_etl.extract import EXPECTED_COLUMNS

logger = logging.getLogger(__name__)
LIST_URL = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-cr257"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) job-market-etl (hoc tap, 1 lan/ngay)",
    "Accept-Language": "vi-VN,vi;q=0.9",
}

RAW_DIR = PROJECT_ROOT / "data" / "raw"

def _clean_city(name: str) -> str:
    return name.replace("(mới)", "").strip()

def parse_job_card(card, crawl_date: date) -> dict:
    title_link = card.select_one("h3.title a")
    title = title_link.select_one("span[title]")
    company = card.select_one(".company-name")
    salary = card.select_one(".title-salary")
    posted = card.select_one("label.label-update")

    address_link = card.select_one("a.address")
    tooltip = BeautifulSoup(address_link.get("title", ""), "html.parser")
    cities = [_clean_city(li.get_text(strip=True)) for li in tooltip.select("li")]
    if not cities:
        cities = [_clean_city(address_link.get_text(strip=True))]

    return {
        "created_date": crawl_date.isoformat(),
        "job_title": title["title"].strip() if title else title_link.get_text(" ", strip=True),
        "company": company.get_text(strip=True) if company else None,
        "salary": salary.get_text(strip=True) if salary else None,
        "address": ": ".join(cities),
        "time": posted.get_text(" ", strip=True) if posted else None,
        "link_description": title_link["href"],
    }

def parse_list_page(html: str, crawl_date: date) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    rows = [parse_job_card(card, crawl_date) for card in soup.select("div.job-item-search-result")]
    return pd.DataFrame(rows, columns=EXPECTED_COLUMNS)    

def fetch_page(session: requests.Session, page: int, timeout: float = 20) -> str:
    response = session.get(LIST_URL, params={"page": page}, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def crawl(crawl_date: date, max_pages: int = 60, delay: float = 3.0, fetch=None) -> pd.DataFrame:
    session = requests.Session()
    fetch = fetch or (lambda page: fetch_page(session, page))
    frames, seen = [], set()
    for page in range(1, max_pages + 1):
        if page > 1:
            time.sleep(delay)
        df = parse_list_page(fetch(page), crawl_date)
        new = df[~df["link_description"].str.split("?").str[0].isin(seen)]
        logger.info("Trang %d: %d tin, %d tin mới", page, len(df), len(new))
        if new.empty:
            break
        seen.update(new["link_description"].str.split("?").str[0])
        frames.append(new)
    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=EXPECTED_COLUMNS)
    logger.info("Crawl xong: %d tin", len(result))
    return result

def save_raw(df: pd.DataFrame, crawl_date: date, raw_dir: Path = RAW_DIR) -> Path:
    path = Path(raw_dir) / f"topcv_{crawl_date.isoformat()}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Đã lưu %s", path)
    return path