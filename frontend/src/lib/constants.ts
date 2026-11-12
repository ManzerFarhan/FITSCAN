// Mirrors backend/app/core/constants.py (BRD §6). Keep both in sync.

export const DOC_TYPES = ["LAB_REPORT"] as const;  // printed lab reports only
export type DocType = (typeof DOC_TYPES)[number];

export const DOCUMENT_STATUSES = [
  "UPLOADED", "PREPROCESSING", "OCR_RUNNING", "EXTRACTING", "NEEDS_VERIFICATION",
  "EXTRACTED", "VERIFIED", "ANALYZED", "FAILED",
] as const;
export type DocumentStatus = (typeof DOCUMENT_STATUSES)[number];
export const PROCESSING_TERMINAL: DocumentStatus[] = ["EXTRACTED", "NEEDS_VERIFICATION", "VERIFIED", "ANALYZED", "FAILED"];

export type ParameterStatus = "WITHIN" | "BELOW" | "ABOVE" | "UNKNOWN";
export type FindingClass = "OUT_OF_RANGE" | "UNCERTAIN" | "URGENT";
export type SourceTag = "EXTRACTED" | "USER_CORRECTED" | "AI_GENERATED";

export const REPORT_CATEGORIES = [
  "CBC", "LFT", "KFT", "LIPID", "THYROID", "SUGAR", "B12", "VITAMIN_D", "IRON", "COAG", "CARDIAC", "HORMONE", "INFLAMMATION", "OTHER",
] as const;
export type ReportCategory = (typeof REPORT_CATEGORIES)[number];

export const CATEGORY_LABELS: Record<string, string> = {
  CBC: "Complete Blood Count", LFT: "Liver Function", KFT: "Kidney Function", LIPID: "Lipid Profile",
  THYROID: "Thyroid", SUGAR: "Sugar / HbA1c", B12: "Vitamin B12 & Folate", VITAMIN_D: "Vitamin D",
  IRON: "Iron Studies", COAG: "Coagulation", CARDIAC: "Heart Markers", HORMONE: "Hormones", INFLAMMATION: "Inflammation & Immunity",
  OTHER: "Other",
};

// Mirrors HealthScoreBand / BmiCategory in backend/app/core/constants.py
export type HealthScoreBand = "MOSTLY_WITHIN" | "SOME_OUTSIDE" | "MANY_OUTSIDE";
export const HEALTH_SCORE_BAND_LABEL: Record<HealthScoreBand, string> = {
  MOSTLY_WITHIN: "Most results within your lab's range",
  SOME_OUTSIDE: "Some results outside your lab's range",
  MANY_OUTSIDE: "Many results outside your lab's range",
};

export type BmiCategory = "UNDERWEIGHT" | "NORMAL" | "OVERWEIGHT" | "OBESE";
export const BMI_CATEGORY_LABEL: Record<BmiCategory, string> = {
  UNDERWEIGHT: "Underweight", NORMAL: "Healthy weight", OVERWEIGHT: "Overweight", OBESE: "Obese",
};
/** WHO adult cut-offs, same as backend health_score.bmi(). */
export function bmiFrom(heightCm: number, weightKg: number): { value: number; category: BmiCategory } {
  const value = Math.round((weightKg / (heightCm / 100) ** 2) * 10) / 10;
  const category: BmiCategory = value < 18.5 ? "UNDERWEIGHT" : value < 25 ? "NORMAL" : value < 30 ? "OVERWEIGHT" : "OBESE";
  return { value, category };
}

export const DISCLAIMER_TEXT =
  "FITSCAN provides general information to help you understand your documents. It does not diagnose conditions, prescribe medication, or replace advice from a qualified doctor. Always consult your doctor.";

export const URGENT_UI_TEXT = "This value is far outside the reference range. Please contact your doctor promptly.";

export const MAX_UPLOAD_MB = 15;
export const ACCEPTED_MIME = ["application/pdf", "image/jpeg", "image/png"];
export const ACCEPTED_EXT = [".pdf", ".jpg", ".jpeg", ".png"];

export const STATUS_STEPS: { key: DocumentStatus; label: string }[] = [
  { key: "UPLOADED", label: "Uploaded" },
  { key: "PREPROCESSING", label: "Preparing" },
  { key: "OCR_RUNNING", label: "Reading text" },
  { key: "EXTRACTING", label: "Extracting" },
  { key: "NEEDS_VERIFICATION", label: "Your review" },
  { key: "VERIFIED", label: "Verified" },
  { key: "ANALYZED", label: "Analysed" },
];

export const ISSUE_LABELS: Record<string, string> = {
  MISSING_VALUE: "Value missing",
  NON_NUMERIC_VALUE: "Value is not a number",
  UNRECOGNIZED_PARAMETER: "Test name not recognised",
  LIKELY_NOT_A_TEST: "Looks like report text, not a test",
  REFERENCE_RANGE_UNPARSED: "Range could not be read",
  REFERENCE_RANGE_MISSING: "No range printed",
  UNIT_UNRECOGNIZED: "Unit not recognised",
  IMPLAUSIBLE_VALUE: "Value looks implausible - check digits",
  POSSIBLE_DECIMAL_ERROR: "Possible decimal-point error",
  AMBIGUOUS_ASSOCIATION: "Unclear which value belongs to this test",
  SEX_SPECIFIC_RANGE: "Range depends on sex - add yours in profile",
};
