import pytest

from app.pipelines.lab_report.normalizer import match_parameter


@pytest.mark.parametrize(
    "raw, pid",
    [
        ("Haemoglobin", "hemoglobin"),
        ("Hemoglobin (Hb)", "hemoglobin"),
        ("HB", "hemoglobin"),
        ("Packed Cell Volume (PCV)", "hematocrit"),
        ("Total Leucocyte Count", "wbc_count"),
        ("TLC", "wbc_count"),
        ("Platelet Count", "platelet_count"),
        ("S.G.O.T", "ast_sgot"),
        ("SGPT (ALT)", "alt_sgpt"),
        ("Serum Creatinine", "creatinine"),
        ("Bilirubin - Total", "bilirubin_total"),
        ("Bilirubin Direct", "bilirubin_direct"),
        ("Cholesterol, Total", "cholesterol_total"),
        ("HDL Cholesterol - Direct", "hdl"),
        ("TSH - Ultrasensitive", "tsh"),
        ("Glycosylated Haemoglobin (HbA1c)", "hba1c"),
        ("Fasting Blood Sugar", "glucose_fasting"),
        ("25-OH Vitamin D", "vitamin_d"),
        ("Vitamin B12", "vitamin_b12"),
        ("Sodium (Na+)", "sodium"),
    ],
)
def test_known_synonyms(raw, pid):
    m = match_parameter(raw)
    assert m.parameter_id == pid, (raw, m)
    assert m.score >= 0.85


def test_fuzzy_typo():
    m = match_parameter("Haemoglobln")
    assert m.parameter_id == "hemoglobin"
    assert m.method == "fuzzy"
    assert m.score < 1.0


def test_unknown_is_not_guessed():
    m = match_parameter("Zinc protoporphyrin ratio xyz")
    assert m.parameter_id is None
    assert m.score == 0.0


def test_short_tokens_not_fuzzy_matched():
    assert match_parameter("Kx").parameter_id is None
