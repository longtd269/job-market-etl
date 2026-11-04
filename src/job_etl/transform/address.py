"""Chuẩn hóa cột address: chuỗi chữ -> locations [(city, district)]."""

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

        if part in CITIES:
            current_city = part
            locations.append((current_city, None))
            continue

        if locations[-1] == (current_city, None):
            locations.pop()

        for district in part.split(","):
            district = district.strip()
            if district:
                locations.append((current_city, district))    

    return locations