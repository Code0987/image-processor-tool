"""Tests for input validators."""
import pytest

from image_ops import is_positive_int_or_empty, is_valid_quality


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", True),
        ("0", True),
        ("42", True),
        ("-1", False),
        ("1.5", False),
        ("abc", False),
        (None, False),
    ],
)
def test_is_positive_int_or_empty(value, expected):
    assert is_positive_int_or_empty(value) is expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", True),
        ("1", True),
        ("100", True),
        ("50", True),
        ("0", False),
        ("101", False),
        ("-5", False),
        ("x", False),
        (None, False),
    ],
)
def test_is_valid_quality(value, expected):
    assert is_valid_quality(value) is expected
