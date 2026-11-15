"""Test chức năng tranform job title"""
import pytest
import pandas as pd
from job_etl.transform.job_title import parse_title, transform_job_title

@pytest.mark.parametrize(
    "title, group",
    [
        ("Lập Trình Viên Java", "Backend"),
        ("Senior .Net (Từ 5-12 Năm Kinh Nghiệm)", "Backend"),
        ("Nhân Viên Front - End", "Frontend"),
        ("Middle JavaScript Developer", "Developer"),
        ("Fullstack Developer (NodeJS, ReactJS)", "Fullstack"),
        ("Chuyên Viên Kiểm Thử Phần Mềm", "Tester / QA"),
        ("Quality Assurance (Up To 12M)", "Tester / QA"),
        ("Data Engineer (Focus Gcp) - Salary Up To $2800", "Data / AI"),
        ("Kỹ Sư Cầu Nối (Brse, N2/N1)", "BrSE / Comtor"),
        ("IT Helpdesk", "IT Support / Hệ thống"),
        ("UI/UX Designer", "Designer"),
        ("Internal Auditor", "Khác"),
    ],
)
def test_group_by_keyword(title, group):
    assert parse_title(title)[0] == group

def test_map_first_role():
    assert parse_title("QA Manager")[0] == "Tester / QA"
    assert parse_title("React Native Developer")[0] == "Mobile"

@pytest.mark.parametrize(
    "title, level",
    [
        ("Thực Tập Sinh Business Analyst", "Intern"),
        ("Fresher Global Java Tại Đà Nẵng", "Fresher"),
        ("Senior AI Engineer - Salary Up To $2500", "Senior"),
        ("Trưởng Nhóm Lập Trình Web", "Lead"),
        ("Lập Trình Viên Backend", None),
    ],
)

def test_job_level(title, level):
    assert parse_title(title)[1] == level

def test_title_empty():
    assert parse_title(None) == ("Khác", None)

def test_transform_add_2_columns():
    df = pd.DataFrame({"row_id": [1, 2], "job_title": ["Senior Java Developer", "Video Editor"]})

    out = transform_job_title(df)

    assert out["job_group"].tolist() == ["Backend", "Khác"]
    assert out["job_level"].tolist() == ["Senior", None]
    assert "job_group" not in df.columns    

