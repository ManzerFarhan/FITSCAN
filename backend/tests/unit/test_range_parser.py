import pytest

from app.pipelines.lab_report.range_parser import parse_range


@pytest.mark.parametrize(
    "raw, low, high, kind",
    [
        ("12-16", 12, 16, "between"),
        ("12.0 - 16.0", 12.0, 16.0, "between"),
        ("13.0 – 17.0", 13.0, 17.0, "between"),
        ("4000 - 11000", 4000, 11000, "between"),
        ("1,50,000 - 4,50,000", 150000, 450000, "between"),
        ("0.4 to 4.0", 0.4, 4.0, "between"),
        ("(3.5-5.2)", 3.5, 5.2, "between"),
        ("12 - 16 g/dL", 12, 16, "between"),
        ("< 200", None, 200, "upper"),
        ("<200", None, 200, "upper"),
        ("<= 5.7", None, 5.7, "upper"),
        ("Less than 150", None, 150, "upper"),
        ("up to 5.0", None, 5.0, "upper"),
        ("Upto 40", None, 40, "upper"),
        ("> 40", 40, None, "lower"),
        (">=60", 60, None, "lower"),
        ("More than 30", 30, None, "lower"),
    ],
)
def test_simple_ranges(raw, low, high, kind):
    r = parse_range(raw)
    assert r.kind == kind
    assert r.low == low
    assert r.high == high
    assert r.raw == raw


def test_exclusive_vs_inclusive_bounds():
    assert parse_range("<200").high_inclusive is False
    assert parse_range("up to 5.0").high_inclusive is True
    assert parse_range(">40").low_inclusive is False
    assert parse_range(">=40").low_inclusive is True


def test_sex_specific_without_sex_is_not_guessed():
    r = parse_range("M: 13-17 F: 12-15")
    assert r.kind == "sex_specific"
    assert r.low is None and r.high is None


@pytest.mark.parametrize(
    "raw, sex, low, high",
    [
        ("M: 13-17 F: 12-15", "M", 13, 17),
        ("M: 13-17 F: 12-15", "F", 12, 15),
        ("Male: 13.0-17.0; Female: 12.0-15.5", "female", 12.0, 15.5),
        ("Men 0.7-1.3 / Women 0.6-1.1", "M", 0.7, 1.3),
    ],
)
def test_sex_specific_with_sex(raw, sex, low, high):
    r = parse_range(raw, sex=sex)
    assert (r.low, r.high) == (low, high)


def test_tiered_range_uses_normal_tier():
    r = parse_range("Desirable: <200 Borderline: 200-239 High: >=240")
    assert r.kind == "upper" and r.high == 200


@pytest.mark.parametrize("raw", [None, "", "See note", "Negative", "16-12"])
def test_unparseable(raw):
    assert parse_range(raw).parsed is False
