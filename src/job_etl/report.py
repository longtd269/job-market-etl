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
    fig.text(0.01, 0.01, "Chỉ tính tin có ghi lương. USD quy đổi 25.000 VND.", fontsize=8, color=TEXT_MUTED)
    return _save(fig, path)

def build_report(engine: Engine, out_dir: Path = FIGURES_DIR) -> list[Path]:
    salaries = read_view(engine, "v_job_salary")
    return [
        plot_salary_by_group(salary_by_group(salaries), out_dir / "1_luong_theo_nhom_nghe.png"),
    ]