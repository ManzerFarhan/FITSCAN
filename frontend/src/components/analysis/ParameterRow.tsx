"use client";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { FindingBadge, SourceBadge, StatusBadge } from "@/components/ui/badges";
import type { AnalysisRow } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ParameterRow({ row, defaultOpen, highlight }: { row: AnalysisRow; defaultOpen?: boolean; highlight?: boolean }) {
  const [open, setOpen] = useState(!!defaultOpen);
  return (
    <li id={`a-${row.row_id}`} className={cn("rounded-lg border bg-white", row.finding_class === "URGENT" ? "border-red-300" : "border-slate-200", highlight && "ring-2 ring-brand-300")}>
      <button className="flex w-full flex-col gap-2 p-3 text-left sm:flex-row sm:items-center" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-slate-900">{row.name}</p>
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-slate-900">{row.value} {row.unit}</span>
            <span className="text-slate-400"> · </span>lab range {row.ref_raw ?? "not printed"}
            {row.lab_flag && <span className="text-slate-500"> · lab flag {row.lab_flag}</span>}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-1">
          <StatusBadge status={row.status} />
          {row.finding_class && row.finding_class !== "OUT_OF_RANGE" && <FindingBadge value={row.finding_class} />}
          <SourceBadge tag={row.value_source} />
          <ChevronDown className={cn("h-4 w-4 text-slate-400 transition", open && "rotate-180")} aria-hidden />
        </div>
      </button>
      {row.urgent_message && (
        <p className="mx-3 mb-3 rounded-md bg-red-50 p-2 text-sm font-medium text-red-800">{row.urgent_message}</p>
      )}
      {open && (
        <div className="border-t border-ai-100 bg-ai-50/60 p-3 text-sm text-slate-700">
          <div className="mb-1"><SourceBadge tag="AI_GENERATED" /></div>
          <p>{row.explanation}</p>
          <p className="mt-1 italic text-slate-600">{row.context}</p>
        </div>
      )}
    </li>
  );
}
