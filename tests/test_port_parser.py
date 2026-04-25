import pytest
from scanner.port_scanner import parse_ports


def test_single_port():
    assert parse_ports("80") == [80]


def test_comma_list():
    assert parse_ports("22,80,443") == [22, 80, 443]


def test_range():
    assert parse_ports("1-5") == [1, 2, 3, 4, 5]


def test_mixed():
    assert parse_ports("22,80,443-445") == [22, 80, 443, 444, 445]


def test_output_is_sorted():
    assert parse_ports("443,22,80") == [22, 80, 443]


def test_deduplication():
    assert parse_ports("80,80,80") == [80]


def test_out_of_range_filtered():
    assert parse_ports("0,80,65536") == [80]


def test_invalid_raises():
    with pytest.raises(ValueError):
        parse_ports("abc")


def test_reversed_range_raises():
    with pytest.raises(ValueError, match="Invalid range"):
        parse_ports("100-1")


def test_range_exceeds_max_raises():
    with pytest.raises(ValueError, match="Invalid range"):
        parse_ports("1-100000")


def test_range_below_min_raises():
    with pytest.raises(ValueError, match="Invalid range"):
        parse_ports("0-5")
