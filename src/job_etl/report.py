import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy.engine import Engine 

from job_etl.config import PROJECT_ROOT
logger = logging.getLogger(__name__)
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
BAR_COLOR = "#2a78d6"
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_MUTED = "#52514e"

def read_view(engine: Engine, name: str) -> pd.DataFrame:
    df = pd.read_sql(f"SELECT * FROM {name}", engine)
    logger.info("Đọc %s: %d dòng", name, len(df))
    return df

def _save(fig, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("Đã lưu %s", path.name)
    return path

def salary_by_group(salaries: pd.DataFrame, min_jobs: int = 10) -> pd.DataFrame:
    summary = (
        salaries.groupby("job_group")["salary_million_vnd"]
        .agg(median_salary="median", n_jobs="count")
        .reset_index()
    )
    summary = summary[summary["n_jobs"] >= min_jobs]
    return summary.sort_values("median_salary", ascending=False).reset_index(drop=True)

def plot_salary_by_group(summary: pd.DataFrame, path: Path) -> Path:
    data = summary.iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6.5), facecolor=SURFACE)
    ax.barh(data["job_group"], data["median_salary"], color=BAR_COLOR, height=0.6)
    for y, (value, n) in enumerate(zip(data["median_salary"], data["n_jobs"])):
        ax.text(value + 0.6, y, f"{value:.1f}  ({n} tin)", va="center", fontsize=9, color=TEXT_MUTED)
    ax.set_xlabel("Lương (triệu VND/tháng)", color=TEXT_MUTED)
    ax.set_xlim(0, data["median_salary"].max() * 1.25)
    ax.tick_params(axis="y", colors=TEXT)
    ax.set_title("Lương theo nhóm nghề", loc="left", fontsize=13, color=TEXT, pad=12)
    fig.text(0.01, 0.01, "USD quy đổi 25.000 VND.", fontsize=8, color=TEXT_MUTED)
    return _save(fig, path)

def  plot_city(area: pd.DataFrame, path: Path, limit: int = 10) -> Path:
    data = area.sort_values("n_jobs", ascending=False).head(limit).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=SURFACE)
    ax.barh(data["city"], data["n_jobs"], color=BAR_COLOR, height=0.6)
    for y, n in enumerate(data["n_jobs"]):
        ax.text(n + 1.5, y, f"{n} tin", va="center", fontsize=9, color=TEXT_MUTED)
    ax.set_xlabel("Số tin theo khu vực địa lý", color=TEXT_MUTED)
    ax.set_xlim(0, data["n_jobs"].max() * 1.3)
    ax.tick_params(axis="y", colors=TEXT)
    ax.set_title(f"Tin theo khu vực", loc="left", fontsize=13, color=TEXT, pad=12)
    return _save(fig, path)

def plot_top_technologies(tech: pd.DataFrame, path: Path, top: int = 15) -> Path:
    data = tech.sort_values("n_jobs", ascending=False).head(top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=SURFACE)
    ax.barh(data["technology"], data["n_jobs"], color=BAR_COLOR, height=0.6)
    for y, n in enumerate(data["n_jobs"]):
        ax.text(n + 1.5, y, f"{n} tin", va="center", fontsize=9, color=TEXT_MUTED)
    ax.set_xlabel("Số tin có nhắc tới công nghệ trong tiêu đề", color=TEXT_MUTED)
    ax.set_xlim(0, data["n_jobs"].max() * 1.3)
    ax.tick_params(axis="y", colors=TEXT)
    ax.set_title(f"Top {top} công nghệ được tuyển nhiều nhất", loc="left", fontsize=13, color=TEXT, pad=12)
    return _save(fig, path)

def build_report(engine: Engine, out_dir: Path = FIGURES_DIR) -> list[Path]:
    salaries = read_view(engine, "v_job_salary")
    area = read_view(engine, "v_area_jobs")
    tech = read_view(engine, "v_technology_jobs")
    return [
        plot_salary_by_group(salary_by_group(salaries), out_dir / "1_luong_theo_nhom_nghe.png"),
        plot_city(area, out_dir / "2_thanh_pho.png"),
        plot_top_technologies(tech, out_dir / "3_top_cong_nghe.png"),
    ]