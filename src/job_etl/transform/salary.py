"""Chuẩn hóa cột salary: chuỗi chữ -> (min_salary, max_salary, salary_unit)."""
import re

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
    if t.startswith("tới") and len(numbers) == 1:
        return None, numbers[0], unit_name
    if t.startswith("trên") and len(numbers) == 1:
        return numbers[0], None, unit_name
    if "-" in t and len(numbers) == 2:
        return numbers[0], numbers[1], unit_name
      

    return None, None, None