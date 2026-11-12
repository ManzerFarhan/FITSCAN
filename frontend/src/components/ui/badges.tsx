import { AlertOctagon, ArrowDown, ArrowUp, Bot, CircleHelp, FileText, PencilLine, ShieldCheck, ShieldQuestion } from "lucide-react";
import type { DocumentStatus, FindingClass, ParameterStatus, SourceTag } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function Badge({ className, children, title }: { className?: string; children: React.ReactNode; title?: string }) {
  return (
    <span title={title} className={cn("inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium", className)}>
      {children}
    </span>
  );
}

/** FR-DASH-9 / BR-05: three visually distinct classes. URGENT is the only one styled as alarming. */
export function FindingBadge({ value }: { value: FindingClass | null }) {
  if (!value) return null;
  if (value === "URGENT")
    return <Badge className="border-red-300 bg-red-600 text-white"><AlertOctagon className="h-3 w-3" />Contact doctor promptly</Badge>;
  if (value === "UNCERTAIN")
    return <Badge className="border-dashed border-slate-400 bg-slate-50 text-slate-700"><CircleHelp className="h-3 w-3" />Needs your check</Badge>;
  return <Badge className="border-amber-300 bg-amber-50 text-amber-800">Outside lab range</Badge>;
}

export function StatusBadge({ status }: { status: ParameterStatus }) {
  const map = {
    WITHIN: { c: "border-green-200 bg-green-50 text-green-800", t: "Within range", I: null },
    ABOVE: { c: "border-amber-300 bg-amber-50 text-amber-800", t: "Above range", I: ArrowUp },
    BELOW: { c: "border-sky-300 bg-sky-50 text-sky-800", t: "Below range", I: ArrowDown },
    UNKNOWN: { c: "border-slate-200 bg-slate-50 text-slate-600", t: "Not compared", I: null },
  }[status];
  const I = map.I;
  return <Badge className={map.c}>{I && <I className="h-3 w-3" aria-hidden />}{map.t}</Badge>;
}

/** BR-10: extracted facts vs AI-generated text are always visibly labelled. */
export function SourceBadge({ tag }: { tag: SourceTag }) {
  if (tag === "AI_GENERATED")
    return <Badge className="border-ai-100 bg-ai-50 text-ai-700" title="Written by AI from verified values and cited sources"><Bot className="h-3 w-3" />AI-generated</Badge>;
  if (tag === "USER_CORRECTED")
    return <Badge className="border-violet-200 bg-violet-50 text-violet-800" title="You corrected this value"><PencilLine className="h-3 w-3" />You corrected</Badge>;
  return <Badge className="border-brand-200 bg-brand-50 text-brand-800" title="Read from your document"><FileText className="h-3 w-3" />Extracted</Badge>;
}

const DOC_STATUS: Record<DocumentStatus, { t: string; c: string }> = {
  UPLOADED: { t: "Uploaded", c: "border-slate-200 bg-slate-50 text-slate-700" },
  PREPROCESSING: { t: "Processing", c: "border-sky-200 bg-sky-50 text-sky-800" },
  OCR_RUNNING: { t: "Reading text", c: "border-sky-200 bg-sky-50 text-sky-800" },
  EXTRACTING: { t: "Extracting", c: "border-sky-200 bg-sky-50 text-sky-800" },
  NEEDS_VERIFICATION: { t: "Needs review", c: "border-amber-300 bg-amber-50 text-amber-800" },
  EXTRACTED: { t: "Ready to confirm", c: "border-brand-200 bg-brand-50 text-brand-800" },
  VERIFIED: { t: "Verified", c: "border-green-200 bg-green-50 text-green-800" },
  ANALYZED: { t: "Analysed", c: "border-ai-100 bg-ai-50 text-ai-700" },
  FAILED: { t: "Failed", c: "border-red-200 bg-red-50 text-red-800" },
};

export function DocStatusBadge({ status }: { status: DocumentStatus }) {
  const s = DOC_STATUS[status] ?? DOC_STATUS.UPLOADED;
  return <Badge className={s.c}>{s.t}</Badge>;
}

export function VerifiedBadge({ verified, note }: { verified: boolean; note?: string }) {
  return verified
    ? <Badge className="border-green-200 bg-green-50 text-green-800" title={note}><ShieldCheck className="h-3 w-3" />Verified listing</Badge>
    : <Badge className="border-slate-300 bg-slate-50 text-slate-600" title={note}><ShieldQuestion className="h-3 w-3" />Unverified</Badge>;
}
