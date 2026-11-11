from job_etl.logger import setup_logging
from job_etl.pipeline import main
from job_etl.db import get_engine
from job_etl.config import PROJECT_ROOT, RAW_DATA_PATH

setup_logging()
raise SystemExit(main())
