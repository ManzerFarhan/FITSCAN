// TS types mirroring backend Pydantic schemas.
import type {
  BmiCategory, DocType, DoctorType, DocumentStatus, FindingClass, HealthScoreBand, ParameterStatus, SourceTag,
} from "./constants";

export interface DocumentOut {
  id: string;
  doc_type: DocType;
  original_filename: string;
  mime: string;
  size_bytes: number;
  pages: number;
  status: DocumentStatus;
  status_message: string | null;
  lab_name: string | null;
  lab_address: string | null;
  patient_name: string | null;
  doctor_name: string | null;
  report_category: string | null;
  report_date: string | null;
  collected_date: string | null;
  report_number: string | null;
  uploaded_at: string;
  description: string | null;
  parameter_count: number;
  out_of_range_count: number;
  needs_verification_count: number;
  has_analysis: boolean;
}

export interface BBox { page: number; x0: number; y0: number; x1: number; y1: number }

export interface ParameterOut {
  id: string;
  position: number;
  parameter_id: string | null;
  canonical_name: string | null;
  name_raw: string;
  value_num: number | null;
  value_raw: string | null;
  unit: string | null;
  unit_normalized: string | null;
  ref_low: number | null;
  ref_high: number | null;
  ref_raw: string | null;
  lab_flag: string | null;
  status: ParameterStatus;
  finding_class: FindingClass | null;
  confidence: number;
  issues: string[];
  needs_verification: boolean;
  bbox_json: BBox | null;
  page_no: number;
  verified: boolean;
  source_tag: SourceTag;
}

export interface ExtractionOut {
  document: DocumentOut;
  metadata: Record<string, { value: string | null; confidence: number }>;
  parameters: ParameterOut[];
  confidence_threshold: number;
  warnings: string[];
  engine: string | null;
}

export interface SourceRef { chunk_id: number; title: string; source: string; url: string; text: string; score: number }

export interface AnalysisRow {
  row_id: string;
  parameter_id: string | null;
  name: string;
  value: string | null;
  value_num: number | null;
  unit: string | null;
  ref_raw: string | null;
  ref_low: number | null;
  ref_high: number | null;
  status: ParameterStatus;
  lab_flag: string | null;
  finding_class: FindingClass | null;
  value_source: SourceTag;
  explanation: string;
  context: string;
  explanation_source: SourceTag;
  urgent_message: string | null;
  source_refs: number[];
}

export interface AnalysisOut {
  id: string;
  document_id: string;
  summary: {
    category: string | null;
    lab_name: string | null;
    report_date: string | null;
    counts: { total: number; verified: number; within: number; below: number; above: number; unknown: number; needs_verification: number };
    parameters: AnalysisRow[];
    excluded: { row_id: string; name: string; reason: string }[];
    urgent: AnalysisRow[];
    doctor_questions: string[];
    generated_by: string;
    disclaimer: string;
  };
  observations: string[];
  sources: SourceRef[];
  model: string;
  prompt_version: string;
  created_at: string;
  source_tag: SourceTag;
}

export interface ChatMessageOut {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceRef[];
  created_at: string;
  source_tag: SourceTag | null;
}

export interface Finding {
  document_id: string;
  parameter_row_id: string;
  parameter_id: string | null;
  name: string;
  value: string | null;
  unit: string | null;
  ref_raw: string | null;
  status: ParameterStatus;
  lab_flag: string | null;
  finding_class: FindingClass;
  verified: boolean;
  report_date: string;
  lab_name: string | null;
  previous: { value: number; date: string; document_id: string; change: number } | null;
}


export interface DashboardData {
  user: { full_name: string | null; is_guest: boolean };
  cards: { total_reports: number; tests_analyzed: number; out_of_range: number; to_review: number };
  latest_report: (DocumentOut & { summary: string }) | null;
  important_findings: Finding[];
  charts?: DashboardCharts;
  health_score?: HealthScore | null;
  bmi?: Bmi | null;
}

export interface HealthScore {
  available: boolean; out_of: number; method: string; reason?: string;
  score?: number; band?: HealthScoreBand; counted?: number;
  within?: number; slightly_outside?: number; well_outside?: number; urgent?: number; excluded_unverified?: number;
  report_date?: string; document_id?: string; lab_name?: string | null;
  previous?: { score: number; report_date: string; document_id: string } | null;
}

export interface Bmi { value: number; category: BmiCategory; height_cm: number; weight_kg: number }

export interface DashboardCharts {
  latest_status: { within: number; below: number; above: number; unknown: number; needs_check: number } | null;
  by_system: { category: string; within: number; outside: number; unknown: number }[];
  trends: {
    parameter_id: string; name: string; unit: string | null; ref_low: number | null; ref_high: number | null; latest_status: string;
    points: { date: string; value: number; status: string; document_id: string }[];
  }[];
}

export interface TermExplanation {
  term: string;
  kind: "test" | "not_a_test" | "unknown";
  explanation: string;
  suggestions: { parameter_id: string; canonical_name: string; score: number }[];
  sources: { chunk_id: number; n: number; title: string; source: string; url: string }[];
  source_tag: "AI_GENERATED";
}

export interface AssistantReply {
  answer: string;
  intent: string;
  actions: { label: string; href: string }[];
  sources: { chunk_id: number; n: number; title: string; source: string; url: string }[];
  suggestions: string[];
  source_tag: "AI_GENERATED";
}

export interface Centre {
  provider_id: string;
  name: string;
  address: string | null;
  locality: string | null;
  city: string | null;
  lat: number;
  lng: number;
  phone: string | null;
  website: string | null;
  maps_url: string | null;
  booking_url: string | null;
  rating: number | null;
  rating_count: number | null;
  hours: string[];
  business_status: string | null;
  categories: string[];
  price: string | null;
  kind: "lab" | "doctor";
}

export interface RankedCentre {
  centre: Centre;
  distance_km: number | null;
  score: number;
  score_breakdown: Record<string, number>;
  verified: boolean;
  verification_note: string;
  test_availability: string;
}

export interface LocationOut { city: string | null; locality: string | null; postal_code: string | null; source: string | null; note: string | null }

export interface CentreSearchResult {
  location: LocationOut;
  origin: { lat: number; lng: number; label: string | null };
  radius_km: number;
  tests: string[];
  doctor_type: DoctorType | null;
  provider: string;
  disclaimer: string;
  results: RankedCentre[];
}

export interface ComparisonPoint {
  document_id: string; date: string; lab_name: string | null; value: number; value_raw: string; unit_raw: string | null;
  ref_low: number | null; ref_high: number | null; ref_raw: string | null; status: ParameterStatus; converted: boolean;
}

export interface ComparedParameter {
  parameter_id: string; name: string; category: string | null; unit: string | null; points: ComparisonPoint[];
  previous: ComparisonPoint; current: ComparisonPoint; absolute_change: number; percent_change: number | null;
  overall_change: number; direction: "higher" | "lower" | "unchanged"; reference_range_changed: boolean;
  transition: "NEWLY_OUTSIDE_RANGE" | "NEWLY_INSIDE_RANGE" | "STILL_OUTSIDE_RANGE" | "NO_RANGE_CHANGE";
}

export interface ComparisonOut {
  id: string;
  document_ids: string[];
  created_at: string;
  disclaimer: string;
  result: {
    documents: { document_id: string; date: string; lab_name: string | null; category: string | null; filename: string }[];
    compared: ComparedParameter[];
    unmatched: { parameter_id?: string; name: string; document_id: string; date: string; reason: string }[];
    non_comparable: { parameter_id: string; name: string; reason: string }[];
    excluded_unverified: number;
    summary: { text: string; doctor_questions: string[]; generated_by: string; source_tag: SourceTag };
  };
}

export interface User {
  id: string; email: string; full_name: string | null; phone: string | null; dob: string | null; gender: string | null;
  preferred_city: string | null; address: string | null; retention_days: number | null; created_at: string;
  height_cm?: number | null; weight_kg?: number | null;
  is_admin?: boolean;  // may open /admin
  admin_role?: "USER" | "ADMIN" | "OWNER";
}

// ---- Admin panel (/admin) ----
export type AdminRole = "USER" | "ADMIN" | "OWNER";
export interface DailyCount { date: string; count: number }
export interface AdminOverview {
  users: number; users_7d: number; active_7d: number; suspended: number; guests_active: number;
  documents: number; documents_7d: number; failed: number; read_success_rate: number | null; parameters: number;
  by_status: Record<string, number>; signups_daily: DailyCount[]; uploads_daily: DailyCount[];
  unrecognised_tests: { name: string; count: number }[];
}
export interface AdminSystem {
  version: string; environment: string; database: string; storage: string; ocr_engine: string; tests_in_dictionary: number;
  chatbot: string; explanations: string; centre_search: string; guest_retention_hours: number; max_upload_mb: number;
  email: string; kb_articles: number; llm_model: string | null; gemini_model: string | null;
}
export interface AdminClient extends Omit<User, "is_admin" | "admin_role"> {
  role: AdminRole; last_login_at: string | null; disabled_at: string | null; documents?: number; last_upload?: string | null;
}
export interface AdminDocument {
  id: string; filename: string; status: DocumentStatus; status_message: string | null; category: string | null;
  lab_name: string | null; report_date: string | null; uploaded_at: string; pages: number; size_bytes: number; mime: string;
  parameters: number; unrecognised: number; out_of_range: number; owner: string; user_id: string | null;
}
export interface AdminDocumentDetail extends AdminDocument {
  patient_name: string | null; doctor_name: string | null; collected_date: string | null; engine: string | null;
  warnings: string[]; results: ParameterOut[];
}
export interface AdminActivity { at: string; action: string; label: string | null; entity: string }
export interface AdminClientDetail { user: AdminClient; documents: AdminDocument[]; activity: AdminActivity[] }
export interface AdminAuditRow extends AdminActivity { entity_id: string | null; user_id: string | null; who: string }
export interface Paged<T> { total: number; items: T[] }
export interface DatasetTest {
  id: string; name: string; category: string; category_label: string; source: "core" | "extended";
  unit: string | null; plausible_min: number | null; plausible_max: number | null; synonyms: string[]; about: string | null;
  kb_articles: number;
  reference: { n: number | null; p2_5: number | null; p50: number | null; p97_5: number | null; unit: string | null; sources: string[] } | null;
}
export interface AdminDataset {
  summary: { tests: number; names: number; categories: number; core: number; extended: number; with_reference: number;
    reference_values: number; kb_articles: number; with_kb: number; units: number };
  sources: { name: string; kind: string; file: string; what: string; used_for: string }[];
  categories: { category: string; label: string; tests: number }[];
  tests: DatasetTest[];
  reference_sources: { source: string; tests: number; values: number }[];
  knowledge: { title: string; source: string; url: string; tests: string[] }[];
}
export interface NameCheck { input: string; recognised: boolean; test_id: string | null; test_name: string | null; category: string | null; confidence: number; method: string }
export interface WeeklySummaryPreview {
  configured: boolean; recipients: string[]; weekday: number; last_sent: string | null; html: string;
  summary: { period: string; new_clients: number; reports: number; failed: number; read_success_rate: number | null };
}
export interface AdminTeamMember extends Partial<AdminClient> { email: string; role: AdminRole; pending?: boolean }

export interface SessionOut { authenticated: boolean; user: User | null; migrated_documents: number }
