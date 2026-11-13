"""Blood-test dictionary + knowledge library consistency, and 'test rows only' reading. Synthetic data only."""
import re

import pytest

from app.pipelines.lab_report.normalizer import match_parameter, normalize_key
from app.pipelines.lab_report.pipeline import build_parameter, is_boilerplate, is_note_or_paragraph
from app.rag.ingest import load_documents
from app.rag.retriever import retrieve
from app.services.analysis_service import about_text
from app.services.assistant_service import explain_term
from app.utils import dictionaries


def test_dictionary_is_large_and_consistent():
    params = dictionaries.parameters()
    assert len(params) >= 450
    owner: dict[str, str] = {}
    for pid, p in params.items():
        assert about_text(pid), f"{pid} has no plain-language description"
        if p.get("plausible_min") is not None and p.get("plausible_max") is not None:
            assert p["plausible_min"] <= p["plausible_max"]
        for s in [p["canonical_name"], *p["synonyms"]]:
            k = normalize_key(s)
            assert owner.setdefault(k, pid) == pid, f"'{s}' belongs to both {owner[k]} and {pid}"


def test_kb_parameter_ids_exist_and_urls_are_https():
    params = dictionaries.parameters()
    docs = load_documents()
    assert len(docs) >= 70
    for d in docs:
        assert d.url.startswith("https://"), d.title
        for pid in d.parameters:
            assert pid in params, f"{d.title}: unknown parameter {pid}"


@pytest.mark.parametrize("name,pid", [
    ("Absolute Neutrophil Count", "neutrophils_abs"), ("Nucleated RBCs", "nrbc"), ("RDW-SD", "rdw_sd"),
    ("PDW", "pdw"), ("Prothrombin Time (PT)", "pt"), ("INR", "inr"), ("APTT", "aptt"), ("D-Dimer", "d_dimer"),
    ("S. Magnesium", "magnesium"), ("TIBC", "tibc"), ("% Transferrin Saturation", "transferrin_sat"),
    ("Anti TPO", "anti_tpo"), ("Fasting Insulin", "insulin_fasting"), ("HOMA-IR", "homa_ir"),
    ("hs-CRP", "hs_crp"), ("CRP", "crp"), ("Lipoprotein (a)", "lpa"), ("Apo B", "apo_b"), ("Troponin I", "troponin_i"),
    ("CPK-MB", "ck_mb"), ("NT-proBNP", "nt_probnp"), ("Vitamin B9 (Folate)", "folate"), ("Total PSA", "psa_total"),
    ("Beta HCG", "beta_hcg"), ("SGOT/SGPT Ratio", "ast_alt_ratio"), ("Immature Granulocytes", "ig_pct"),
])
def test_common_report_names_are_recognised(name, pid):
    assert match_parameter(name).parameter_id == pid


def test_new_categories_drive_dashboard_groups():
    p = dictionaries.parameters()
    assert p["pt"]["category"] == "COAG" and p["ferritin"]["category"] == "IRON" and p["crp"]["category"] == "INFLAMMATION"


@pytest.mark.parametrize("line", [
    "Note: Results should be correlated clinically",
    "Interpretation: values between 5.7 and 6.4 indicate increased risk",
    "Comments - Kindly correlate with clinical findings",
    "Clinical significance: HbA1c reflects average glucose over 3 months",
    "* Test performed on fully automated analyser",
    "Method: Photometry",
    "Please note that the reference ranges are age and sex specific for this assay 2024",
    "The results pertain to the sample tested and are subject to the conditions mentioned overleaf",
])
def test_notes_and_paragraphs_are_not_tests(line):
    assert is_note_or_paragraph(line, matched=match_parameter(line).parameter_id is not None) or is_boilerplate(line)


@pytest.mark.parametrize("name", ["Haemoglobin", "Absolute Lymphocyte Count", "Total Leucocyte Count (TLC)",
                                  "Glycosylated Haemoglobin (HbA1c)", "Packed Cell Volume"])
def test_real_test_rows_are_kept(name):
    assert not is_boilerplate(name)
    assert not is_note_or_paragraph(name, matched=match_parameter(name).parameter_id is not None)


def test_footer_rows_are_skipped():
    for line in ["Test Performed at :7091 - DEMO LAB 3 Floor, Plot No 1", "Booking Centre :5498 - Demo Health Pvt Ltd",
                 "The authenticity of the report can be verified by scanning the Q R Code", "Page 1 of 11"]:
        assert is_boilerplate(line), line


def test_status_uses_lab_range_for_new_tests():
    p = build_parameter(0, "Absolute Neutrophil Count", "5.53", "10^9/L", "2.0-7.0", None, 0.99, None, 1, 0.85)
    assert p.parameter_id == "neutrophils_abs" and p.status == "WITHIN" and "UNIT_UNRECOGNIZED" not in p.issues
    q = build_parameter(0, "INR", "1.1", None, "0.8 - 1.2", None, 0.99, None, 1, 0.85)
    assert q.status == "WITHIN"


@pytest.mark.parametrize("query,title_word", [
    ("what is INR", "Prothrombin"), ("transferrin saturation meaning", "Iron tests"), ("troponin", "Troponin"),
    ("what does Bio Ref Interval mean", "Reading a lab report"), ("units 10^9/L cumm lakhs", "Units"),
    ("SGPT high", "ALT"), ("anti TPO antibodies", "Thyroid antibody"),
])
def test_library_retrieval(query, title_word):
    hits = retrieve(query, k=3)
    assert any(title_word.lower() in h.title.lower() for h in hits), [h.title for h in hits]


def test_explain_term_for_new_tests():
    r = explain_term("Total Iron Binding Capacity")
    assert r.suggestions[0].parameter_id == "tibc" and r.sources
    assert re.search(r"\[S\d\]", r.explanation)


@pytest.mark.parametrize("name,pid", [  # extended dictionary (scripts/build_extended_dictionary.py)
    ("CEA", "cea"), ("CA 19-9", "ca199"), ("CA-125", "ca125"), ("Alpha Feto Protein (AFP)", "afp"),
    ("HBsAg", "hbsag"), ("HIV I & II Antibody", "hiv"), ("Anti HCV", "anti_hcv"), ("S. Typhi 'O'", "widal_o"),
    ("Dengue NS1 Antigen", "dengue_ns1"), ("Pus Cells", "pus_cells"), ("Specific Gravity", "urine_sg"),
    ("Epithelial Cells", "epithelial_cells"), ("Ketone Bodies", "urine_ketones"), ("Urine Microalbumin", "urine_microalbumin"),
    ("Albumin/Creatinine Ratio", "urine_acr"), ("Anti CCP", "anti_ccp"), ("ANA (IFA)", "ana"), ("pCO2", "pco2"),
    ("Base Excess", "base_excess"), ("Fructosamine", "fructosamine"), ("IgE Total", "ige_total"), ("Complement C3", "complement_c3"),
    ("Blood Group (ABO)", "blood_group"), ("Rh Factor", "rh_type"), ("HbA2", "hb_a2"), ("Thyroglobulin", "thyroglobulin"),
    ("SHBG", "shbg"), ("Free Testosterone", "free_testosterone"), ("Selenium", "selenium"), ("CD4 Count", "cd4"),
])
def test_extended_report_names_are_recognised(name, pid):
    assert match_parameter(name).parameter_id == pid
