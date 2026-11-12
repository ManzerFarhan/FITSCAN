import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";
import { StatusBadge } from "@/components/ui/badges";
import type { ComparedParameter } from "@/lib/types";
import { fmtNum, formatDate } from "@/lib/utils";

const TRANSITION: Record<string, string> = {
  NEWLY_OUTSIDE_RANGE: "Newly outside the lab's range",
  NEWLY_INSIDE_RANGE: "Moved inside the lab's range",
  STILL_OUTSIDE_RANGE: "Still outside the lab's range",
  NO_RANGE_CHANGE: "",
};

/** FR-HIST-4 previous-vs-current. Neutral wording only (BR-09): higher / lower / unchanged. */
export function PrevCurrentCards({ items }: { items: ComparedParameter[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {items.map((c) => {
        const Icon = c.direction === "higher" ? ArrowUpRight : c.direction === "lower" ? ArrowDownRight : ArrowRight;
        return (
          <div key={c.parameter_id} className="rounded-lg border border-slate-200 bg-white p-3">
            <p className="font-medium text-slate-900">{c.name}</p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-xs text-slate-500">Previous · {formatDate(c.previous.date)}</p>
                <p className="font-semibold">{fmtNum(c.previous.value)} <span className="font-normal text-slate-500">{c.unit}</span></p>
                <StatusBadge status={c.previous.status} />
              </div>
              <div>
                <p className="text-xs text-slate-500">Current · {formatDate(c.current.date)}</p>
                <p className="font-semibold">{fmtNum(c.current.value)} <span className="font-normal text-slate-500">{c.unit}</span></p>
                <StatusBadge status={c.current.status} />
              </div>
            </div>
            <p className="mt-2 flex items-center gap-1 text-sm text-slate-700">
              <Icon className="h-4 w-4" aria-hidden />
              {c.direction === "unchanged" ? "Unchanged" : `${c.direction === "higher" ? "Higher" : "Lower"} by ${fmtNum(Math.abs(c.absolute_change))} ${c.unit ?? ""}`}
              {c.percent_change !== null && c.direction !== "unchanged" && ` (${Math.abs(c.percent_change)}%)`}
            </p>
            {TRANSITION[c.transition] && <p className="mt-1 text-xs text-slate-500">{TRANSITION[c.transition]}</p>}
            {c.current.converted || c.previous.converted ? <p className="mt-1 text-xs text-slate-400">Units converted for comparison</p> : null}
          </div>
        );
      })}
    </div>
  );
}
