"""BR-01: status is always computed from the report's own reference range."""
import pytest

from app.core.constants import ParameterStatus as S
from app.pipelines.lab_report.range_parser import parse_range
from app.pipelines.lab_report.status_calculator import compute_status, normalize_lab_flag


@pytest.mark.parametrize(
    "value, raw, expected",
    [
        (14, "12-16", S.WITHIN),
        (12, "12-16", S.WITHIN),
        (16, "12-16", S.WITHIN),
        (11.9, "12-16", S.BELOW),
        (16.1, "12-16", S.ABOVE),
        (199, "<200", S.WITHIN),
        (200, "<200", S.ABOVE),
        (5.0, "up to 5.0", S.WITHIN),
        (39, ">40", S.BELOW),
        (40, ">40", S.BELOW),
        (40, ">=40", S.WITHIN),
        (14, "See note", S.UNKNOWN),
        (None, "12-16", S.UNKNOWN),
    ],
)
def test_status(value, raw, expected):
    assert compute_status(value, parse_range(raw)) == expected


def test_br01_lab_range_wins_over_typical_range():
    # Hemoglobin 12.5 is "normal" in many textbooks, but THIS lab says 13-17 -> BELOW.
    assert compute_status(12.5, parse_range("13-17")) == S.BELOW
    # And a lab with an unusual range is respected too.
    assert compute_status(12.5, parse_range("11-13")) == S.WITHIN


def test_sex_specific_unknown_without_sex():
    assert compute_status(14, parse_range("M: 13-17 F: 12-15")) == S.UNKNOWN


@pytest.mark.parametrize("raw, flag", [("H", "H"), ("high", "H"), ("L", "L"), ("HH", "HH"), ("*", "*"), ("", None), ("x", None)])
def test_lab_flags_preserved(raw, flag):
    assert normalize_lab_flag(raw) == flag
