"""Single source of truth for enums & statuses (BRD §6). Mirrored in frontend/src/lib/constants.ts."""
from enum import StrEnum


class DocType(StrEnum):
    LAB_REPORT = "LAB_REPORT"  # printed lab reports only (doctor's prescriptions were removed)


class DocumentStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PREPROCESSING = "PREPROCESSING"
    OCR_RUNNING = "OCR_RUNNING"
    EXTRACTING = "EXTRACTING"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    EXTRACTED = "EXTRACTED"  # all fields above confidence threshold, awaiting user confirmation
    VERIFIED = "VERIFIED"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


# Statuses at which background processing has stopped (BRD §5 polling contract).
PROCESSING_TERMINAL = {
    DocumentStatus.EXTRACTED,
    DocumentStatus.NEEDS_VERIFICATION,
    DocumentStatus.VERIFIED,
    DocumentStatus.ANALYZED,
    DocumentStatus.FAILED,
}


class ParameterStatus(StrEnum):
    WITHIN = "WITHIN"
    BELOW = "BELOW"
    ABOVE = "ABOVE"
    UNKNOWN = "UNKNOWN"


class FindingClass(StrEnum):
    OUT_OF_RANGE = "OUT_OF_RANGE"
    UNCERTAIN = "UNCERTAIN"
    URGENT = "URGENT"


class SourceTag(StrEnum):
    EXTRACTED = "EXTRACTED"
    USER_CORRECTED = "USER_CORRECTED"
    AI_GENERATED = "AI_GENERATED"


class ReportCategory(StrEnum):
    CBC = "CBC"
    LFT = "LFT"
    KFT = "KFT"
    LIPID = "LIPID"
    THYROID = "THYROID"
    SUGAR = "SUGAR"
    B12 = "B12"
    VITAMIN_D = "VITAMIN_D"
    IRON = "IRON"
    COAG = "COAG"
    CARDIAC = "CARDIAC"
    HORMONE = "HORMONE"
    INFLAMMATION = "INFLAMMATION"
    OTHER = "OTHER"


class HealthScoreBand(StrEnum):
    """Dashboard lab score band - describes the share of results within the lab's range, never a diagnosis (BR-04)."""
    MOSTLY_WITHIN = "MOSTLY_WITHIN"   # score >= 8.5
    SOME_OUTSIDE = "SOME_OUTSIDE"     # 6.0 - 8.4
    MANY_OUTSIDE = "MANY_OUTSIDE"     # < 6.0


class BmiCategory(StrEnum):
    """WHO adult BMI categories."""
    UNDERWEIGHT = "UNDERWEIGHT"  # < 18.5
    NORMAL = "NORMAL"            # 18.5 - 24.9
    OVERWEIGHT = "OVERWEIGHT"    # 25 - 29.9
    OBESE = "OBESE"              # >= 30


ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

DISCLAIMER_TEXT = (
    "FITSCAN provides general information to help you understand your documents. "
    "It does not diagnose conditions, prescribe medication, or replace advice from a "
    "qualified doctor. Always consult your doctor."
)

URGENT_UI_TEXT = (
    "This value is far outside the reference range. Please contact your doctor promptly."
)
