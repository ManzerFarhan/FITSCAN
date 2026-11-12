import pytest

from app.utils.units import convert, normalize_unit, units_compatible


@pytest.mark.parametrize(
    "raw, norm",
    [
        ("mg/dl", "mg/dL"), ("MG/DL", "mg/dL"), ("gm/dl", "g/dL"), ("g%", "g/dL"), ("IU/L", "U/L"),
        ("uIU/mL", "µIU/mL"), ("μIU/mL", "µIU/mL"), ("mIU/L", "µIU/mL"), ("/cumm", "/µL"),
        ("cells/cumm", "/µL"), ("10^3/uL", "10^3/µL"), ("Lakhs/cumm", "lakh/µL"),
        ("million/cumm", "10^6/µL"), ("fl", "fL"), ("mm/1st hr", "mm/hr"), ("ng / ml", "ng/mL"),
        ("weird-unit", "weird-unit"), ("", None), (None, None),
    ],
)
def test_normalize_unit(raw, norm):
    assert normalize_unit(raw) == norm


def test_identity_conversion():
    assert convert(5.0, "mg/dl", "mg/dL") == 5.0


def test_glucose_mmol_to_mgdl():
    assert convert(5.5, "mmol/L", "mg/dL", "glucose_fasting") == pytest.approx(99.09, rel=1e-3)
    assert convert(99.088, "mg/dL", "mmol/L", "glucose_fasting") == pytest.approx(5.5, rel=1e-3)


def test_parameter_specific_factors_do_not_leak():
    # mmol/L -> mg/dL for glucose must NOT be used for cholesterol
    assert convert(5.0, "mmol/L", "mg/dL", "cholesterol_total") == pytest.approx(193.35, rel=1e-3)
    assert convert(5.0, "mmol/L", "mg/dL", None) is None


def test_cell_count_conversions():
    assert convert(7500, "/cumm", "10^3/µL", "wbc_count") == pytest.approx(7.5)
    assert convert(2.5, "lakhs/cumm", "10^3/µL", "platelet_count") == pytest.approx(250)
    assert convert(250000, "/cumm", "lakhs/cumm", "platelet_count") == pytest.approx(2.5)


def test_vitamin_d_nmol():
    assert convert(75, "nmol/L", "ng/mL", "vitamin_d") == pytest.approx(30.0, rel=1e-2)


def test_incompatible_units():
    assert not units_compatible("mg/dL", "%", "hba1c")
    assert units_compatible("mIU/L", "uIU/mL", "tsh")
