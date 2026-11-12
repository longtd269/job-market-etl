"""Chuẩn hóa cột salary: chuỗi chữ -> (min_salary, max_salary, salary_unit)."""
import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)


SALARY_COLUMNS = ["min_salary", "max_salary", "salary_unit"]


UNIT_FACTOR = {"triệu": 1000000, "usd": 1}
UNIT_NAME = {"triệu": "VND", "usd": "USD"}

#Func return min_salary, max_salary, unit 
def parse_salary(raw) -> tuple:

    if raw is None:
        return None, None, None
    
    t = " ".join(str(raw).split()).strip().lower()

    if t in ("thoả thuận", "thỏa thuận", "", "nan"):
        return None, None, None

    #extract unit salary
    unit_match = re.search(r"(triệu|usd)$", t)
    if unit_match is None:
        return None, None, None
    
    unit = unit_match.group(1)
    unit_factor = UNIT_FACTOR[unit]
    unit_name = UNIT_NAME[unit]

    #extract numbers salary
    numbers = re.findall(r"\d[\d,.]*", t)
    numbers = [
        float(i.replace(",", "")) * unit_factor
        for i in numbers
    ]

    #extract by condition text
    #max_salary
    if t.startswith(("tới", "đến", "up to", "dưới")) and len(numbers) == 1:
        return None, numbers[0], unit_name
    if t.startswith(("trên", "từ", "from")) and len(numbers) == 1:
        return numbers[0], None, unit_name
    if "-" in t and len(numbers) == 2:
        return numbers[0], numbers[1], unit_name
      

    return None, None, None


def _safe_parse(raw):
    try:
        return (*parse_salary(raw), None)
    except ValueError as e:
        return (None, None, None, str(e))
    
def transform_salary(df: pd.DataFrame) -> pd.DataFrame:
    cols = [*SALARY_COLUMNS, "salary_error"]
    out = df.copy()
    out[cols] = pd.DataFrame(df["salary"].apply(_safe_parse).tolist(), index=df.index, columns=cols)
    out[["min_salary", "max_salary"]] = out[["min_salary", "max_salary"]].astype("float")

    n_error = out["salary_error"].notna().sum()
    logger.info("Salary: %s", out["salary_unit"].value_counts(dropna=False).to_dict())
    if n_error:
        logger.warning("Salary: %d dòng không parse được", n_error)
    return out      