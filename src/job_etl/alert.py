"""Push noti on discord job detail info"""
import os
import logging
from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

USD_TO_VND = 25000
MAX_EMBEDS = 10 
MAX_EMBED_CHARS = 6000
EMBED_COLOR = 0x2A78D6

NEW_JOBS_SQL = """
SELECT
    j.job_id, j.job_title, j.company, j.job_group, j.job_level,
    j.salary, j.min_salary, j.max_salary, j.salary_unit, j.link_description,
    GROUP_CONCAT(DISTINCT l.city ORDER BY l.location_order SEPARATOR ', ') AS cities
FROM jobs AS j
LEFT JOIN job_locations AS l ON l.job_id = j.job_id
WHERE j.first_seen = :batch_date
GROUP BY j.job_id
"""

def _parse_tuple(env_key: str, default: tuple) -> tuple[str, ...]:
    val = os.getenv(env_key)
    if val is None:
        return default
    return tuple(item.strip() for item in val.split(",") if item.strip())

def _parse_bool(env_key: str, default: bool) -> bool:
    val = os.getenv(env_key)
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "on")

CRITERIA = {
    "job_groups": _parse_tuple("JOB_ALERT_GROUPS", ("Data / AI")),
    "cities": _parse_tuple("JOB_ALERT_CITIES", ()),
    "min_salary_million": float(os.getenv("JOB_ALERT_MIN_SALARY", 0)),
    "include_negotiable": _parse_bool("JOB_ALERT_INCLUDE_NEGOTIABLE", True)
}

def read_new_jobs(engine: Engine, batch_date: date) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(NEW_JOBS_SQL), conn, params={"batch_date": batch_date})

def salary_million(df: pd.DataFrame) -> pd.Series:
    low = pd.to_numeric(df["min_salary"], errors="coerce").astype(float)
    high = pd.to_numeric(df["max_salary"], errors="coerce").astype(float)
    value = ((low + high) / 2).fillna(low).fillna(high)
    rate = df["salary_unit"].map({"USD": USD_TO_VND}).fillna(1)
    return value * rate / 1000000

def filter_jobs(jobs: pd.DataFrame, criteria: dict | None = CRITERIA) -> pd.DataFrame:
    out = jobs.copy()
    out["salary_million"] = salary_million(out)

    if criteria is not None:
        job_groups = criteria.get("job_groups", ())
        in_group = out["job_group"].isin(job_groups) if job_groups else True

        target_cities = criteria.get("cities", ())
        if target_cities:
            cities = out["cities"].fillna("").str.split(", ")
            in_city = cities.apply(lambda cs: any(c in target_cities for c in cs))
        else:
            in_city = True

        min_salary = criteria.get("min_salary_million", 0)
        enough_pay = out["salary_million"] >= min_salary
        if criteria.get("include_negotiable", False):
            enough_pay |= out["salary_million"].isna()
        out = out[in_group & in_city & enough_pay]

    return out.sort_values(["salary_million", "job_id"], ascending=[False, True], na_position="last")  

def _field(name: str, value) -> dict:
    value = "—" if value is None or pd.isna(value) or str(value).strip() == "" else str(value)
    return {"name": name, "value": value[:1024], "inline": True}

def embed_chars(embed: dict) -> int:
    fields = sum(len(f["name"]) + len(f["value"]) for f in embed.get("fields", []))
    return len(embed.get("title", "")) + len(embed.get("description", "")) + fields

def fit_embed_limit(embeds: list[dict], limit: int = MAX_EMBED_CHARS) -> list[dict]:
    for embed in reversed(embeds):
        if sum(embed_chars(e) for e in embeds) <= limit:
            break
        embed.pop("description", None)
    return embeds

def build_alert_payload(matched: pd.DataFrame, batch_date: date, criteria: dict | None = None, summaries: dict[int, str] | None = None) -> dict | None:
    if matched.empty:
        return None

    summaries = summaries or {}
    shown = matched.head(MAX_EMBEDS)
    summary = (
        f"🔔 **{len(matched)} tin mới** ngày {batch_date} sắp xếp theo lương"
        + (
            f"\n({', '.join(criteria.get("job_groups", ()))} · {', '.join(criteria.get("cities", ()))} · từ {criteria.get("min_salary_million", 0):g} triệu)"
            if criteria is not None
            else ""
        )
    )
    if len(matched) > len(shown):
        summary += f"\nHiện {len(shown)} tin lương cao nhất, còn {len(matched) - len(shown)} tin nữa trong DB."
    embeds = [
        {
            "title": str(row.job_title)[:256],
            "url": row.link_description,
            "color": EMBED_COLOR,
            "fields": [
                _field("Công ty", row.company),
                _field("Lương", row.salary),
                _field("Địa chỉ", row.cities),
                _field("Nhóm", row.job_group if pd.isna(row.job_level) else f"{row.job_group} · {row.job_level}"),
            ],
        }
        for row in shown.itertuples()
    ]
    for embed, job_id in zip(embeds, shown["job_id"]):
        if summaries.get(int(job_id)):
            embed["description"] = summaries[int(job_id)][:4096]
    return {"content": summary, "embeds": fit_embed_limit(embeds)}