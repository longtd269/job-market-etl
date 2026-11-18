# Job Market ETL – Mini project Data Engineer

Làm sạch, xây pipeline ETL và phân tích dữ liệu tin tuyển dụng IT (TopCV, 1.933 tin, ngày 2023-08-01).

## Dữ liệu đầu vào – `data/raw/jobs.csv`

| Cột             | Ví dụ                                                                            | Ghi chú                                    |
| ---------------- | ---------------------------------------------------------------------------------- | ------------------------------------------- |
| created_date     | 2023-08-01                                                                         |                                             |
| job_title        | .Net Developer (N3) \| T9160                                                       | Rất lộn xộn, cần gom nhóm              |
| company          | Công ty Cổ Phần Rikkeisoft                                                      |                                             |
| salary           | `Thoả thuận`, `10 - 20 triệu`, `Tới 2,000 USD`, `Trên 8 triệu`       | 710 tin "Thoả thuận"; có cả VND và USD |
| address          | `Hà Nội: Cầu Giấy`, `Hà Nội: Thanh Xuân: Hải Dương: TP Hải Dương` | Có thể nhiều địa điểm                |
| time             | Còn 25 ngày để ứng tuyển                                                     |                                             |
| link_description | https://www.topcv.vn/...                                                           |                                             |

## Cấu trúc thư mục

```
job-market-etl/
├── data/
│   ├── raw/              # Dữ liệu gốc (không sửa)
│   └── processed/        # Dữ liệu sau khi làm sạch (không commit)
├── src/job_etl/          # Code chính: config, transform, pipeline...
├── tests/                # Unit test (pytest)
├── scripts/              # Script tiện ích (check_env.py)
├── notebooks/            # Notebook khám phá dữ liệu
├── reports/figures/      # Biểu đồ xuất ra
├── logs/                 # Log khi chạy pipeline
├── docker-compose.yml    # MySQL 8.4
├── requirements.txt
├── .env.example          # Mẫu cấu hình (copy thành .env)
└── pytest.ini
```

## Cài đặt

Yêu cầu: Python 3.11+ (đã thử với 3.13), Docker (OrbStack hoặc Docker Desktop), Git.

```bash
# 1. Môi trường ảo Python
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 2. Cấu hình
cp .env.example .env               # Windows: copy .env.example .env
# sửa MYSQL_PASSWORD và MYSQL_ROOT_PASSWORD trong .env

# 3. Khởi động MySQL
docker compose up -d
docker compose ps                  # chờ trạng thái "healthy"

# 4. Kiểm tra
python scripts/check_env.py
pytest
```

Kết nối DB bằng tay (MySQL Workbench, DBeaver, SQLTools): host `127.0.0.1`, port `3306`, user/password/database theo file `.env`.
Hoặc dùng mysql client trong container: `docker exec -it job_etl_mysql mysql -u job_etl -p jobs`

MySQL được cấu hình `utf8mb4` để lưu đúng tiếng Việt, và giới hạn `innodb-buffer-pool-size=256M` cho máy RAM thấp (chiếm khoảng 200 MB khi chạy).

Dừng DB: `docker compose down` (thêm `-v` nếu muốn xóa luôn dữ liệu).

**Run pipeline**

Run với raw html(save html thủ công, lưu save bằng tay về)
`python scripts/run_pipeline.py --html-dir data/raw/html/2026-11-12 --date 2026-11-12`

Run với crawl
`python scripts/run_pipeline.py --crawl`

**Cronjob hàng ngày để crawl tin mới:(ví dụ 7h sáng hàng ngày)**

`0 7 * * * /path/job-market-etl/scripts/run_pipeline.sh --crawl >> /path/job-market-etl/logs/cron.log 2>&1`

**Push thông báo tới discord khi chạy pipeline**

Thêm web hook url vào env: `DISCORD_WEBHOOK_URL`

Nếu khi chạy pipeline không muốn gửi thông báo thì thêm flag `--no-notify`

**Push alert list jobs tới discord**

Thêm web hook url vào env: `DISCORD_JOB_ALERT_WEBHOOK_URL`

Chạy script: `python scripts/run_job_alert.py --date <ngày> --no-jd`

`--no-jd` tắt phần lấy JD