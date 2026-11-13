import { CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { FindingBadge, StatusBadge } from "@/components/ui/badges";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Empty } from "@/components/ui/misc";
import { URGENT_UI_TEXT } from "@/lib/constants";
import type { Finding } from "@/lib/types";
import { cn, fmtNum, formatDate } from "@/lib/utils";

/** FR-DASH-5/9: three classes rendered distinctly; only URGENT (validated rules) looks alarming. */
export function ImportantFindings({ findings }: { findings: Finding[] }) {
  return (
    <Card id="findings">
      <CardHeader>
        <div>
          <CardTitle>Important Findings</CardTitle>
          <CardDescription>Values outside your lab's own reference range, lab flags, and values that need your check.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {findings.length === 0 ? (
          <Empty icon={<CheckCircle2 className="h-8 w-8" />} title="Nothing to highlight">Findings from your reports will appear here.</Empty>
        ) : (
          <ul className="divide-y divide-slate-100">
            {findings.map((f) => (
              <li key={f.parameter_row_id}>
                <Link href={`/analysis?doc=${f.document_id}&param=${f.parameter_row_id}`}
                  className={cn("-mx-2 flex flex-col gap-1 rounded-lg px-2 py-3 hover:bg-slate-50 sm:flex-row sm:items-center sm:gap-3",
                    f.finding_class === "URGENT" && "border-l-4 border-red-500 bg-red-50/50")}>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-slate-900">
                      {f.name} <span className="font-normal text-slate-600">{f.value} {f.unit}</span>
                    </p>
                    <p className="text-xs text-slate-500">
                      Lab range {f.ref_raw ?? "not printed"}{f.lab_flag ? ` · lab flag ${f.lab_flag}` : ""} · {formatDate(f.report_date)}
                      {f.previous && ` · previous ${fmtNum(f.previous.value)} (${formatDate(f.previous.date)}), change ${f.previous.change > 0 ? "+" : ""}${fmtNum(f.previous.change)}`}
                    </p>
                    {f.finding_class === "URGENT" && <p className="mt-1 text-sm font-medium text-red-700">{URGENT_UI_TEXT}</p>}
                  </div>
                  <div className="flex shrink-0 flex-wrap gap-1">
                    {f.finding_class !== "UNCERTAIN" && <StatusBadge status={f.status} />}
                    {f.finding_class !== "OUT_OF_RANGE" && <FindingBadge value={f.finding_class} />}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
