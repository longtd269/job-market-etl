import logging
import pandas as pd
import sys
import re

logger = logging.getLogger(__name__)

OTHER_GROUP = "Khác"

GROUP_RULES = [
    ("BrSE / Comtor", r"brse|cầu nối|comtor|phiên dịch"),
    ("Tester / QA", r"tester|\btest|kiểm thử|\bqa\b|\bqc\b|quality assurance"),
    ("Data / AI", r"\bdata|\bdba\b|\bai\b|machine learning|\bml\b|\bbi\b|business intelligence|dữ liệu"),
    ("DevOps / Cloud", r"devops|\bcloud\b|\bsre\b"),
    ("Mobile", r"mobile|android|\bios\b|flutter|react native"),
    ("Game", r"\bgame\b|unity"),
    ("Fullstack", r"full[\s-]*stack"),
    ("Frontend", r"front[\s-]*end|\breact|vue|angular"),
    ("Backend", r"back[\s-]*end|\bjava\b|\.net|\bphp\b|python|golang|\bnode|ruby|\bc#"),
    ("Embedded", r"embedded|nhúng|firmware"),
    ("Business Analyst", r"business analyst|\bba\b|phân tích nghiệp vụ"),
    ("Project / Product Manager", r"project manager|product manager|product owner|\bpm\b|\bpo\b|scrum master"),
    ("Designer", r"designer|\bui\b|\bux\b|thiết kế"),
    ("IT Support / Hệ thống", r"helpdesk|hỗ trợ|support|hệ thống|system|network|\bmạng\b|phần cứng|kỹ thuật"),
    ("Developer", r"developer|lập trình|engineer|kỹ sư|programmer"),
]

LEVEL_RULES = [
    ("Intern", r"intern|thực tập"),
    ("Fresher", r"fresher"),
    ("Lead", r"leader|\blead\b|trưởng nhóm|trưởng phòng|\bhead\b"),
    ("Senior", r"senior|\bsr\b"),
    ("Middle", r"middle|\bmid\b"),
    ("Junior", r"junior|\bjr\b"),
]

TECH_RULES = [
    ("Java", r"\bjava\b"),
    ("JavaScript", r"javascript|\bjs\b"),
    ("React", r"\breact"),
    ("Node.js", r"\bnode"),
    (".NET", r"\.net|\bc#"),
    ("Python", r"python"),
    ("PHP", r"php"),
]

#Func return list locations(city, district) 
#Data sample
# ("Thực Tập Sinh Business Analyst", "Intern"),
# ("Fresher Global Java Tại Đà Nẵng", "Fresher"),
# ("Senior AI Engineer - Salary Up To $2500", "Senior"),
# ("Trưởng Nhóm Lập Trình Web", "Lead"),
# ("Lập Trình Viên Backend", None),

def _check_rule(title: str, rules: list) -> str | None:
    for name, rule in rules:
        if re.search(rule, title):
            return name
    return None    


def parse_title(title) -> tuple[ str, str| None ]:
    if title is None or pd.isna(title):
        return (OTHER_GROUP, None)
    
    text = " ".join(str(title).split()).lower()

    job_group = _check_rule(text, GROUP_RULES) or OTHER_GROUP

    job_level = _check_rule(text, LEVEL_RULES)

    return (job_group, job_level)

def transform_job_title(df: pd.DataFrame) -> pd.DataFrame:
    jobs = df.copy()
    result = pd.DataFrame(
        [parse_title(t) for t in df["job_title"]],
        index=df.index,
        columns=["job_group", "job_level"],
    )

    jobs[["job_group", "job_level"]] = result

    n_other = (jobs["job_group"] == OTHER_GROUP).sum()
    
    logger.info("Có tổng cộng %d nhóm nghề, số lượng %d nhóm ngành tiêu chuẩn, số lượng %d nhóm ngành khác", jobs["job_group"].nunique(), jobs["job_group"].count() - n_other, n_other)
    return jobs
       
def extract_technologies(title) -> list[str]:
    if title is None or pd.isna(title):
        return []
    text = " ".join(str(title).split()).lower()
    return [name for name, pattern in TECH_RULES if re.search(pattern, text)]

def transform_technologies(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for job_id, job_title in zip(df["id"], df["job_title"]):
        data = extract_technologies(job_title)
        for item in data:
            rows.append((job_id, item))
           
    technologies = pd.DataFrame(rows, columns=["job_id", "technology"])
    logger.info("Technologies: %d tin -> %d dòng job_technologies", len(df), len(technologies))

    return technologies



