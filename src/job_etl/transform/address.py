import logging
import pandas as pd
import sys
import unicodedata


logger = logging.getLogger(__name__)

LOCATION_COLUMNS = ["row_id", "location_order", "city", "district"]

"""Chuẩn hóa cột address: chuỗi chữ -> locations [(city, district)]."""
CITY_ALIASES = {"Huế": "Thừa Thiên Huế"}
COUNTRIES = {"Nhật Bản", "Hàn Quốc", "Singapore", "Đài Loan", "Trung Quốc"}  

CITIES = {
    "Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ",
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu", "Bắc Ninh",
    "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước", "Bình Thuận", "Cà Mau",
    "Cao Bằng", "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp",
    "Gia Lai", "Hà Giang", "Hà Nam", "Hà Tĩnh", "Hải Dương", "Hậu Giang",
    "Hoà Bình", "Hưng Yên", "Khánh Hoà", "Kiên Giang", "Kon Tum", "Lai Châu",
    "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", "Nghệ An",
    "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên", "Quảng Bình", "Quảng Nam",
    "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sóc Trăng", "Sơn La", "Tây Ninh",
    "Thái Bình", "Thái Nguyên", "Thanh Hoá", "Thừa Thiên Huế", "Tiền Giang",
    "Trà Vinh", "Tuyên Quang", "Vĩnh Long", "Vĩnh Phúc", "Yên Bái",
    "Nước Ngoài", "Toàn Quốc",
}

def _city_key(name: str) -> str:
    s = unicodedata.normalize("NFD", name.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.lower().replace("-", " ").split())

CITY_LOOKUP = {_city_key(c): c for c in CITIES}
CITY_LOOKUP |= {_city_key(a): c for a, c in CITY_ALIASES.items()}
CITY_LOOKUP |= {_city_key(c): "Nước Ngoài" for c in COUNTRIES}

#Func return list locations(city, district) 
#Data sample
"""Hà Nội: Hồ Chí Minh: Đà Nẵng                                                     
Hồ Chí Minh: Phú Nhuận: Đà Nẵng: Thanh Khê                                  
Nước Ngoài: Hà Nội: Nam Từ Liêm""" 

def parse_address(raw) -> list:
    if raw is None:
        return []

    locations = []
    current_city = None

    for part in str(raw).split(":"):
        part = " ".join(str(part).split())

        city = CITY_LOOKUP.get(_city_key(part))    
        if city is not None:
            current_city = city
            locations.append((current_city, None))
            continue

        if locations and locations[-1] == (current_city, None):
            locations.pop()

        for district in part.split(","):
            district = district.strip()
            if district:
                locations.append((current_city, district))    

    return locations


def transform_address(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    errors = []
    for row_id, address in zip(df["row_id"], df["address"]):
        try:
           data = parse_address(address)
           errors.append(None)
        except Exception as e:
           data = []
           errors.append(e)
           
        for order, item in enumerate(data, start=1):
            (city, district) = item
            rows.append((row_id, order, city, district))       

    jobs = df.copy()
    jobs["address_error"] = errors  
    locations = pd.DataFrame(rows, columns=LOCATION_COLUMNS)
    logger.info("số lượng tin %d số lượng dòng location %d", len(df), len(locations))
    n_error = jobs["address_error"].notna().sum()
    if n_error:
        print("Address: %d dòng không parse được", n_error)
        logger.warning("Address: %d dòng không parse được", n_error)
    return jobs, locations