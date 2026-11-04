"""Test chức năng tranform address field"""
import pytest
from job_etl.transform.address import parse_address

def test_city_only():
    assert parse_address("Hà Nội") == [("Hà Nội", None)]


def test_city_and_district():
    assert parse_address("Hà Nội: Cầu Giấy") == [("Hà Nội", "Cầu Giấy")]


def test_many_districts_in_one_city():
    assert parse_address("Hồ Chí Minh: Quận 2, Quận 12") == [
        ("Hồ Chí Minh", "Quận 2"),
        ("Hồ Chí Minh", "Quận 12"),
    ]


def test_many_cities_with_districts():
    assert parse_address("Hà Nội: Thanh Xuân: Hải Dương: TP Hải Dương") == [
        ("Hà Nội", "Thanh Xuân"),
        ("Hải Dương", "TP Hải Dương"),
    ]


def test_many_cities_without_district():
    assert parse_address("Hà Nội: Hồ Chí Minh: Đà Nẵng") == [
        ("Hà Nội", None),
        ("Hồ Chí Minh", None),
        ("Đà Nẵng", None),
    ]


def test_messy_spaces():
    assert parse_address("  Hà Nội :  Cầu Giấy ,Thanh Xuân ") == [
        ("Hà Nội", "Cầu Giấy"),
        ("Hà Nội", "Thanh Xuân"),
    ]