"""Push noti on discord"""
import os
import logging
from datetime import date
import requests

logger = logging.getLogger(__name__)

DISCORD_LIMIT = 2000
MAX_ERROR_CHARS = 1500 

def build_message(code: int, batch_date: date, seconds: float,
                  counts: dict[str, int] | None = None, error: str | None = None) -> str:
    from job_etl.pipeline import EXIT_OK

    if code == EXIT_OK:
        counts = counts or {}
        lines = [
            f"✅ **Pipeline thành công** – batch {batch_date} ({seconds:.1f}s)",
            f"Tin mới: **{counts.get('new_jobs', 0)}** · cập nhật: {counts.get('updated_jobs', 0)}",
            f"Đang tuyển: {counts.get('active_jobs', 0)} · tổng: {counts.get('total_jobs', 0)}",
        ]
    else:
        error = error or "Không rõ lỗi"
        if len(error) > MAX_ERROR_CHARS:
            error = error[:MAX_ERROR_CHARS] + "…"
        lines = [
            f"❌ **Pipeline thất bại** (exit {code}) – batch {batch_date} ({seconds:.1f}s)",
            f"```{error}```",
            "Xem chi tiết trong logs/pipeline.log",
        ]
    return "\n".join(lines)


def post_webhook(payload: dict, webhook_url: str | None = None, env_var: str = "DISCORD_WEBHOOK_URL",
                 post=requests.post, timeout: float = 10) -> bool:

    webhook_url = webhook_url or os.getenv(env_var)
    if not webhook_url:
        logger.info("Chưa cấu hình %s, bỏ qua thông báo", env_var)
        return False
    try:
        response = post(webhook_url, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Gửi thông báo Discord thất bại: %s", exc)
        return False
    logger.info("Đã gửi thông báo Discord")
    return True

def send_discord(text: str, webhook_url: str | None = None, post=requests.post, timeout: float = 10) -> bool:
    return post_webhook({"content": text}, webhook_url, "DISCORD_WEBHOOK_URL", post=post, timeout=timeout)
