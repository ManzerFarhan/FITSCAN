import { SourceBadge } from "@/components/ui/badges";
import type { ComparisonOut } from "@/lib/types";
import { formatDate } from "@/lib/utils";

/** FR-HIST-5: AI comparison summary + timeline + what could not be compared. */
export function ComparisonSummary({ comparison }: { comparison: ComparisonOut }) {
  const r = comparison.result;
  return (
    <div className="space-y-4">
      <ol className="flex flex-wrap items-center gap-2 text-sm" aria-label="Timeline">
        {r.documents.map((d, i) => (
          <li key={d.document_id} className="flex items-center gap-2">
            <span className="rounded-full bg-slate-100 px-3 py-1">{formatDate(d.date)} · {d.lab_name ?? d.filename}</span>
            {i < r.documents.length - 1 && <span className="text-slate-400">→</span>}
          </li>
        ))}
      </ol>
      <section className="rounded-lg border border-ai-100 bg-ai-50/60 p-4">
        <div className="mb-2 flex items-center gap-2"><h3 className="font-semibold text-slate-900">Summary of changes</h3><SourceBadge tag="AI_GENERATED" /></div>
        <p className="text-sm text-slate-700">{r.summary.text}</p>
        {r.summary.doctor_questions.length > 0 && (
          <>
            <p className="mt-3 text-sm font-medium text-slate-900">Questions for your doctor</p>
            <ol className="list-decimal space-y-0.5 pl-5 text-sm text-slate-700">{r.summary.doctor_questions.map((q) => <li key={q}>{q}</li>)}</ol>
          </>
        )}
      </section>
      {(r.non_comparable.length > 0 || r.unmatched.length > 0 || r.excluded_unverified > 0) && (
        <details className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
          <summary className="cursor-pointer font-medium text-slate-700">Not compared ({r.non_comparable.length + r.unmatched.length})</summary>
          <ul className="mt-2 space-y-1 text-slate-600">
            {r.non_comparable.map((x) => <li key={`nc-${x.parameter_id}`}><strong>{x.name}</strong>: {x.reason}</li>)}
            {r.unmatched.map((x, i) => <li key={`u-${i}`}><strong>{x.name}</strong> ({formatDate(x.date)}): {x.reason}</li>)}
            {r.excluded_unverified > 0 && <li>{r.excluded_unverified} unverified value(s) were left out.</li>}
          </ul>
        </details>
      )}
    </div>
  );
}
