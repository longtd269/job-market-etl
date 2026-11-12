import sys
from pathlib import Path

from bs4 import BeautifulSoup

src = Path(sys.argv[1])
soup = BeautifulSoup(src.read_text(encoding="utf-8"), "html.parser")

cards = soup.select("div.job-item-search-result")
print("Trang có", len(cards), "thẻ tin")

def n_cities(card):
    tooltip = BeautifulSoup(card.select_one("a.address").get("title", ""), "html.parser")
    return len(tooltip.select("li"))

def salary(card):
    return card.select_one(".title-salary").get_text(strip=True)

picked = [
    cards[0],
    next(c for c in cards if n_cities(c) >= 2),
    next(c for c in cards if salary(c).startswith("Từ")),
]

body = "\n".join(str(c) for c in picked)
out = Path("tests/fixtures/topcv_list_sample.html")
out.parent.mkdir(parents=True, exist_ok=True)

out.write_text(
    '<!doctype html>\n<html><head><meta charset="utf-8"></head>\n<body>\n'
    f'<div class="job-list-search-result">\n{body}\n</div>\n</body></html>\n',
    encoding="utf-8",
)

print("Đã ghi", out, f"({out.stat().st_size // 1024} KB)")