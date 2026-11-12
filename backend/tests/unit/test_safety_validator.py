"""BR-04 / FR-AI-5 guardrails, including adversarial outputs an LLM might produce (P3-30)."""
import pytest

from app.rag.safety_validator import generate_safely, validate

UNSAFE = [
    ("You have diabetes based on this HbA1c.", "diagnosis"),
    ("You likely have anemia.", "diagnosis"),
    ("This value indicates hypothyroidism.", "diagnosis"),
    ("These results are consistent with fatty liver.", "diagnosis"),
    ("You are diabetic.", "diagnosis"),
    ("You were diagnosed with kidney disease.", "diagnosis"),
    ("You should take vitamin D supplements.", "treatment"),
    ("Start taking metformin.", "treatment"),
    ("Stop your medication until you see a doctor.", "treatment"),
    ("I recommend taking iron tablets.", "treatment"),
    ("Take 60000 IU weekly.", "dosage"),
    ("A dose of 500 mg twice a day is typical.", "dosage"),
    ("You should get a thyroid ultrasound scan.", "additional_tests"),
    ("Consider getting an HbA1c test.", "additional_tests"),
    ("Further tests are needed.", "additional_tests"),
    ("This is a medical emergency.", "urgency"),
    ("Go to the hospital now.", "urgency"),
    ("Your potassium is dangerously high.", "urgency"),
]

SAFE = [
    "Hemoglobin measures the oxygen-carrying protein in red blood cells. Your value of 11.2 g/dL is below the lab's reference range (12.0 - 15.0) [S1].",
    "Your total cholesterol of 212 mg/dL is above the lab's range of <200 mg/dL.",
    "FITSCAN does not diagnose conditions. Please discuss your results with your doctor.",
    "HbA1c reflects average blood sugar over roughly the past 2-3 months [S2].",
    "What could explain my TSH being above the lab's range?",
    "Values that are outside the range are not, by themselves, a diagnosis.",
]


@pytest.mark.parametrize("text, category", UNSAFE)
def test_unsafe_text_is_blocked(text, category):
    r = validate(text, "chat")
    assert not r.ok
    assert category in {v.category for v in r.violations}


@pytest.mark.parametrize("text", SAFE)
def test_safe_text_passes(text):
    r = validate(text, "analysis")
    assert r.ok, r.violations


def test_judgement_language_blocked_in_comparisons():  # BR-09
    assert not validate("Your LDL has improved since March.", "comparison").ok
    assert not validate("HDL got worse.", "comparison").ok
    assert validate("LDL is 12 mg/dL lower than in March.", "comparison").ok


def test_generate_safely_regenerates_then_falls_back():
    calls = []

    def bad(feedback):
        calls.append(feedback)
        return "You have diabetes."

    text, used = generate_safely(bad, lambda: "SAFE FALLBACK", "chat")
    assert text == "SAFE FALLBACK" and used is False
    assert len(calls) == 2 and calls[1]  # second attempt received violation feedback


def test_generate_safely_accepts_fixed_output():
    outputs = iter(["Start taking metformin.", "Please discuss this value with your doctor."])
    text, used = generate_safely(lambda fb: next(outputs), lambda: "x", "chat")
    assert used and text.startswith("Please discuss")
