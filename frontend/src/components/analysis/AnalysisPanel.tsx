"use client";
import { Bot, ChevronDown, ExternalLink, Lock, MapPin, MessageCircleQuestion, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { UnlockReminder } from "@/components/layout/LoginToUnlock";
import { SourceBadge } from "@/components/ui/badges";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Spinner } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import { CATEGORY_LABELS } from "@/lib/constants";
import type { AnalysisOut, DocumentOut } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";
import { DownloadSummaryButton } from "./DownloadSummaryButton";
import { ParameterRow } from "./ParameterRow";

const TEASER_POINTS = [
  "Each verified value explained in plain language",
  "Which values sit outside your lab's own range",
  "Questions you could ask your doctor",
  "Trusted health sources behind every explanation, plus a PDF summary",
];

/** Shown before upload: visible from the start, faded and locked until a lab report is attached. */
export function AnalysisTeaser({ attached }: { attached: boolean }) {
  return (
    <Card className={cn("border-ai-100 transition duration-300", !attached && "opacity-50 grayscale")} aria-disabled={!attached}>
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2"><Bot className="h-5 w-5 text-ai-600" />2. AI Medical Report Analysis</CardTitle>
          <CardDescription>
            {attached
              ? "Next: press Upload & process, check the values we read, and your analysis will be ready."
              : "Upload a lab report to unlock your analysis."}
          </CardDescription>
        </div>
        {!attached && <Lock className="h-5 w-5 text-slate-400" aria-label="Locked" />}
      </CardHeader>
      <CardContent className="space-y-4">
        <ul className="grid gap-2 sm:grid-cols-2">
          {TEASER_POINTS.map((t) => (
            <li key={t} className="flex items-start gap-2 rounded-lg bg-ai-50/60 p-3 text-sm text-slate-700">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-ai-600" aria-hidden />{t}
            </li>
          ))}
        </ul>
        <Button variant="ai" size="lg" disabled className="w-full sm:w-auto">
          {attached ? <Sparkles className="h-4 w-4" /> : <Lock className="h-4 w-4" />}Check AI Medical Report Analysis
        </Button>
      </CardContent>
    </Card>
  );
}

/** FR-AI-1..4, 9: opened by the "Check AI Medical Report Analysis" button. */
export function AnalysisPanel({ doc, focusParamId, onAnalyzed }: { doc: DocumentOut; focusParamId?: string | null; onAnalyzed?: () => void }) {
  const [analysis, setAnalysis] = useState<AnalysisOut | null>(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [remind, setRemind] = useState(false);
  const { user } = useAuth();
  const ready = doc.status === "VERIFIED" || doc.status === "ANALYZED";

  useEffect(() => {
    if (!doc.has_analysis) return;
    api<AnalysisOut>(`/documents/${doc.id}/analysis`).then((a) => { setAnalysis(a); if (focusParamId) setOpen(true); }).catch(() => undefined);
  }, [doc.id, doc.has_analysis, focusParamId]);

  const run = async () => {
    setBusy(true); setError(null);
    try {
      setAnalysis(await api<AnalysisOut>(`/documents/${doc.id}/analysis`, { method: "POST" }));
      setOpen(true);
      onAnalyzed?.();
      if (!user) setTimeout(() => setRemind(true), 1500);  // guests: "log in to unlock more" after they see their result
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The analysis could not be generated.");
    } finally { setBusy(false); }
  };

  if (!analysis) {
    return (
      <Card id="ai-analysis" className="border-ai-100">
        <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
          <Bot className="h-10 w-10 text-ai-600" aria-hidden />
          <p className="max-w-md text-sm text-slate-600">
            {ready ? "Get a plain-language explanation of your verified values, with sources." : "Confirm the extracted values above to unlock the AI analysis."}
          </p>
          <Button variant="ai" size="lg" disabled={!ready || busy} onClick={run}>
            {busy ? <Spinner /> : <Sparkles className="h-4 w-4" />}Check AI Medical Report Analysis
          </Button>
          {error && <Alert tone="error">{error}</Alert>}
        </CardContent>
      </Card>
    );
  }

  const s = analysis.summary;
  const c = s.counts;
  return (
    <Card id="ai-analysis" className="border-ai-100">
      <UnlockReminder open={remind} onClose={() => setRemind(false)} />
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2"><Bot className="h-5 w-5 text-ai-600" />AI Medical Report Analysis</CardTitle>
          <CardDescription>
            {CATEGORY_LABELS[s.category ?? ""] ?? s.category ?? "Lab report"} · {s.lab_name ?? "Lab"} · {formatDate(s.report_date)}
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
          {open ? "Collapse" : "Expand"}<ChevronDown className={`h-4 w-4 transition ${open ? "rotate-180" : ""}`} />
        </Button>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-3 gap-2 text-center sm:grid-cols-6">
          {[["Total", c.total, "text-slate-900"], ["Verified", c.verified, "text-slate-900"], ["Within", c.within, "text-green-700"],
            ["Below", c.below, "text-sky-700"], ["Above", c.above, "text-amber-700"], ["Need check", c.needs_verification, "text-slate-500"]].map(([l, v, t]) => (
            <div key={l as string} className="rounded-lg bg-slate-50 p-2"><p className={`text-xl font-bold ${t}`}>{v as number}</p><p className="text-xs text-slate-500">{l as string}</p></div>
          ))}
        </div>
        {s.urgent.length > 0 && (
          <Alert tone="error" title="Please contact your doctor promptly">
            {s.urgent.map((u) => <p key={u.row_id}><strong>{u.name}</strong>: {u.urgent_message}</p>)}
            <p className="mt-1 text-xs">This alert comes from validated lab safety rules, not from the AI.</p>
          </Alert>
        )}
        {open && (
          <>
            {analysis.observations.length > 0 && (
              <section className="rounded-lg border border-ai-100 bg-ai-50/60 p-4">
                <div className="mb-2 flex items-center gap-2"><h3 className="font-semibold text-slate-900">Key observations</h3><SourceBadge tag="AI_GENERATED" /></div>
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">{analysis.observations.map((o) => <li key={o}>{o}</li>)}</ul>
              </section>
            )}
            <section>
              <h3 className="mb-2 font-semibold text-slate-900">Parameter by parameter</h3>
              <ul className="space-y-2">
                {s.parameters.map((r) => <ParameterRow key={r.row_id} row={r} defaultOpen={r.row_id === focusParamId || r.status !== "WITHIN"} highlight={r.row_id === focusParamId} />)}
              </ul>
              {s.excluded.length > 0 && (
                <p className="mt-2 text-xs text-slate-500">Not analysed (not verified): {s.excluded.map((e) => e.name).join(", ")}</p>
              )}
            </section>
            {s.doctor_questions.length > 0 && (
              <section className="rounded-lg border border-ai-100 bg-ai-50/60 p-4">
                <div className="mb-2 flex items-center gap-2">
                  <MessageCircleQuestion className="h-4 w-4 text-ai-600" /><h3 className="font-semibold text-slate-900">Questions to ask your doctor</h3><SourceBadge tag="AI_GENERATED" />
                </div>
                <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-700">{s.doctor_questions.map((q) => <li key={q}>{q}</li>)}</ol>
              </section>
            )}
            {/* BR-11: citations stay available, but collapsed so they don't crowd the page. */}
            <details className="text-xs text-slate-500">
              <summary className="cursor-pointer">
                {analysis.sources.length ? `Based on ${analysis.sources.length} trusted health sources (MedlinePlus, NIH) - show` : "No sources were retrieved for this analysis."}
              </summary>
              <ol className="mt-2 space-y-1">
                {analysis.sources.map((src, i) => (
                  <li key={src.chunk_id}>
                    <a href={src.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-700 hover:underline">
                      [S{i + 1}] {src.title} - {src.source}<ExternalLink className="h-3 w-3" />
                    </a>
                  </li>
                ))}
              </ol>
              <p className="mt-2 text-slate-400">Written by {analysis.model === "fitscan-template" ? "FITSCAN's offline explainer" : analysis.model}</p>
            </details>
          </>
        )}
        <div className="flex flex-wrap gap-2">
          <DownloadSummaryButton docId={doc.id} />
          <Link href={`/tests?doc=${doc.id}`} className={buttonVariants({ variant: "secondary" })}><MapPin className="h-4 w-4" />Find centres for these tests</Link>
          <Button variant="ghost" onClick={run} disabled={busy}>{busy && <Spinner />}Regenerate</Button>
        </div>
      </CardContent>
    </Card>
  );
}
