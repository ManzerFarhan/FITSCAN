import { AlertTriangle, CheckCircle2, Gauge, Info } from "lucide-react";
import Link from "next/link";
import { LoginToUnlock } from "@/components/layout/LoginToUnlock";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { HEALTH_SCORE_BAND_LABEL } from "@/lib/constants";
import type { HealthScore } from "@/lib/types";
import { formatDate } from "@/lib/utils";

// Status palette (good / warning / serious / critical); every segment is also named in the legend.
const PARTS = [
  { key: "within", label: "Within range", color: "#16a34a" },
  { key: "slightly_outside", label: "Slightly outside", color: "#d97706" },
  { key: "well_outside", label: "Well outside", color: "#ea580c" },
  { key: "urgent", label: "Needs prompt attention", color: "#dc2626" },
] as const;

export function HealthScoreCard({ data, locked }: { data?: HealthScore | null; locked?: boolean }) {
  const ok = data?.available && data.score !== undefined;
  const BandIcon = data?.band === "MOSTLY_WITHIN" ? CheckCircle2 : AlertTriangle;
  const bandTone = data?.band === "MOSTLY_WITHIN" ? "text-emerald-700" : data?.band === "SOME_OUTSIDE" ? "text-amber-700" : "text-orange-700";
  return (
    <Card aria-labelledby="health-score-title">
      <CardHeader>
        <div>
          <CardTitle id="health-score-title" className="flex items-center gap-2"><Gauge className="h-5 w-5 text-brand-700" aria-hidden />Lab health score</CardTitle>
          <CardDescription>
            {ok ? <>From your latest confirmed lab report{data.report_date ? ` (${formatDate(data.report_date)})` : ""}, compared with your lab&apos;s own ranges.</>
              : "A quick summary of your latest confirmed lab report, out of 10."}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {locked ? (
          <LoginToUnlock feature="your lab health score" compact
            description="See your latest confirmed report summarised out of 10, compared with your lab's own ranges." />
        ) : !ok ? (
          <div className="flex flex-col items-start gap-2 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
            <p><span className="text-3xl font-bold text-slate-400">–</span><span className="text-slate-400"> / 10</span></p>
            <p>{data?.reason ?? "Upload a lab report to see your score."}</p>
            <Link href="/analysis" className="font-medium text-brand-700 underline">Upload or check a lab report</Link>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-end gap-x-4 gap-y-1">
              <p className="leading-none" aria-label={`Score ${data.score} out of 10`}>
                <span className="text-5xl font-bold tabular-nums text-slate-900">{data.score!.toFixed(1)}</span>
                <span className="text-lg text-slate-500"> / 10</span>
              </p>
              {data.band && (
                <p className={`flex items-center gap-1.5 pb-1 text-sm font-medium ${bandTone}`}>
                  <BandIcon className="h-4 w-4" aria-hidden />{HEALTH_SCORE_BAND_LABEL[data.band]}
                </p>
              )}
            </div>

            <div>
              <div className="flex h-3 w-full gap-0.5 overflow-hidden rounded-full bg-slate-100" role="img"
                aria-label={PARTS.map((p) => `${data[p.key] ?? 0} ${p.label.toLowerCase()}`).join(", ")}>
                {PARTS.map((p) => (data[p.key] ?? 0) > 0 && (
                  <div key={p.key} style={{ width: `${((data[p.key] ?? 0) / data.counted!) * 100}%`, background: p.color }} title={`${p.label}: ${data[p.key]}`} />
                ))}
              </div>
              <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
                {PARTS.map((p) => (
                  <li key={p.key} className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: p.color }} aria-hidden />
                    {p.label} <span className="font-semibold tabular-nums text-slate-900">{data[p.key] ?? 0}</span>
                  </li>
                ))}
              </ul>
            </div>

            <p className="text-xs text-slate-500">
              Based on {data.counted} confirmed result{data.counted === 1 ? "" : "s"}
              {data.lab_name ? ` from ${data.lab_name}` : ""}
              {data.excluded_unverified ? `; ${data.excluded_unverified} unconfirmed value${data.excluded_unverified === 1 ? " was" : "s were"} left out` : ""}.
              {data.previous && <> Previous report ({formatDate(data.previous.report_date)}): <span className="font-semibold text-slate-700">{data.previous.score.toFixed(1)} / 10</span>.</>}
            </p>

            {(data.urgent ?? 0) > 0 && (
              <p className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                <span>{data.urgent} result{data.urgent === 1 ? " is" : "s are"} far outside the range. Please contact your doctor promptly. <a href="#findings" className="font-medium underline">See important findings</a></span>
              </p>
            )}
          </>
        )}
        {!locked && (
          <details className="text-xs text-slate-500">
            <summary className="flex cursor-pointer items-center gap-1 font-medium text-slate-600"><Info className="h-3.5 w-3.5" aria-hidden />How is this calculated?</summary>
            <p className="mt-1">{data?.method}</p>
            <p className="mt-1">This score only summarises how your results compare with the ranges printed on your report. It is not a diagnosis or a measure of your overall health - please discuss your results with your doctor.</p>
          </details>
        )}
      </CardContent>
    </Card>
  );
}
