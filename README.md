# Job Market ETL – Mini project Data Engineer

Làm sạch, xây pipeline ETL và phân tích dữ liệu tin tuyển dụng IT (TopCV, 1.933 tin, ngày 2023-08-01).

## Dữ liệu đầu vào – `data/raw/jobs.csv`

| Cột | Ví dụ | Ghi chú |
|---|---|---|
| created_date | 2023-08-01 | |
| job_title | .Net Developer (N3) \| T9160 | Rất lộn xộn, cần gom nhóm |
| company | Công ty Cổ Phần Rikkeisoft | |
| salary | `Thoả thuận`, `10 - 20 triệu`, `Tới 2,000 USD`, `Trên 8 triệu` | 710 tin "Thoả thuận"; có cả VND và USD |
| address | `Hà Nội: Cầu Giấy`, `Hà Nội: Thanh Xuân: Hải Dương: TP Hải Dương` | Có thể nhiều địa điểm |
| time | Còn 25 ngày để ứng tuyển | |
| link_description | https://www.topcv.vn/... | |

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
├── docker-compose.yml    # PostgreSQL 16
├── requirements.txt
├── .env.example          # Mẫu cấu hình (copy thành .env)
└── pytest.ini
```

## Cài đặt

Yêu cầu: Python 3.11+ (đã thử với 3.13), Docker Desktop, Git.

```bash
# 1. Môi trường ảo Python
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Cấu hình
cp .env.example .env               # Windows: copy .env.example .env
# sửa POSTGRES_PASSWORD trong .env

# 3. Khởi động PostgreSQL
docker compose up -d
docker compose ps                  # chờ trạng thái "healthy"

# 4. Kiểm tra
python scripts/check_env.py
pytest
```

Kết nối DB bằng tay (DBeaver/psql): host `localhost`, port `5432`, user/password/db theo file `.env`.
Hoặc: `docker exec -it job_etl_postgres psql -U job_etl -d jobs`

Dừng DB: `docker compose down` (thêm `-v` nếu muốn xóa luôn dữ liệu).

## Lộ trình

- [x] Bước 0: Setup môi trường
- [ ] Yêu cầu 1: Chuẩn hóa & làm sạch (salary, address, job_title)
- [ ] Yêu cầu 2: Pipeline ETL CSV → PostgreSQL, lập lịch, xử lý lỗi
- [ ] Yêu cầu 3: Phân tích & trực quan hóa
