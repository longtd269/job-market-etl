import logging
import time
from datetime import date
from pathlib import Path

import pandas as pd
from curl_cffi import requests
from bs4 import BeautifulSoup

from job_etl.config import PROJECT_ROOT
from job_etl.extract import EXPECTED_COLUMNS

logger = logging.getLogger(__name__)
LIST_URL = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-cr257"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://google.com",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Upgrade-Insecure-Requests": "1",
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
    response = session.get(LIST_URL, params={"page": page}, timeout=timeout)
    response.raise_for_status()
    return response.text


def crawl(crawl_date: date, max_pages: int = 40, delay: float = 3.0, fetch=None, cache_dir=None) -> pd.DataFrame:
    session = requests.Session(impersonate="chrome")
    fetch = fetch or (lambda page: fetch_page(session, page))
    cache_dir = Path(cache_dir or RAW_DIR / "html" / crawl_date.isoformat())
    cache_dir.mkdir(parents=True, exist_ok=True)
    frames, seen = [], set()
    for page in range(1, max_pages + 1):
        cached = cache_dir / f"page_{page:02d}.html"
        if cached.exists():
            html = cached.read_text(encoding="utf-8")
        else:    
            if page > 1:
                time.sleep(delay)
            html = fetch(page)
            cached.write_text(html, encoding="utf-8")
        df = parse_list_page(html, crawl_date)
        new = df[~df["link_description"].str.split("?").str[0].isin(seen)]
        logger.info("Trang %d: %d tin, %d tin mới", page, len(df), len(new))
        if new.empty:
            break
        seen.update(new["link_description"].str.split("?").str[0])
        frames.append(new)
    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=EXPECTED_COLUMNS)
    logger.info("Crawl xong: %d tin", len(result))
    session.close()
    return result

def save_raw(df: pd.DataFrame, crawl_date: date, raw_dir: Path = RAW_DIR) -> Path:
    path = Path(raw_dir) / f"topcv_{crawl_date.isoformat()}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Đã lưu %s", path)
    return path


# Backup cannot crawl form website
# Read raw html file 
def read_saved_pages(html_dir: Path, crawl_date: date) -> pd.DataFrame:
    files = sorted(Path(html_dir).glob("*.html"))
    if not files:
        raise FileNotFoundError(f"Empty file im {html_dir}")
    frames = []
    for path in files:
        df = parse_list_page(path.read_text(encoding="utf-8"), crawl_date)
        logger.info("%s: %d post", path.name, len(df))
        frames.append(df)
    result = pd.concat(frames, ignore_index=True)

    result = result[~result["link_description"].str.split("?").str[0].duplicated()]
    logger.info("Đọc xong %d file: %d tin không trùng", len(files), len(result))
    return result.reset_index(drop=True)
