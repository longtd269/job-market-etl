"""Test chức năng tranform salary field"""
import pytest
from job_etl.transform.salary import parse_salary

def test_range_vnd():
    assert parse_salary("10 - 20 triệu") == (10000_000, 20000000, "VND")

def test_up_to_usd():
        assert parse_salary("Tới 2,000 USD") == (None, 2000, "USD")


def test_from_vnd():
    assert parse_salary("Trên 8 triệu") == (8000000, None, "VND")


def test_negotiable():
    assert parse_salary("Thoả thuận") == (None, None, None)


def test_extra_spaces_and_uppercase():
    assert parse_salary("  10  -  20   TRIỆU ") == (10000000, 20000000, "VND")