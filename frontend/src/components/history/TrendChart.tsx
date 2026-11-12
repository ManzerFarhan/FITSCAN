"use client";
import { CartesianGrid, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ComparedParameter } from "@/lib/types";
import { fmtNum, formatDate } from "@/lib/utils";

/** FR-HIST-4: value over time with the lab's reference range as a band (latest report's range). */
export function TrendChart({ param }: { param: ComparedParameter }) {
  const data = param.points.map((p) => ({ date: p.date, label: formatDate(p.date), value: p.value, lab: p.lab_name, status: p.status }));
  const lo = param.current.ref_low, hi = param.current.ref_high;
  const values = data.map((d) => d.value).concat([lo ?? NaN, hi ?? NaN].filter((x) => !Number.isNaN(x)));
  const min = Math.min(...values), max = Math.max(...values);
  const pad = (max - min || Math.abs(max) || 1) * 0.2;
  const domain: [number, number] = [Math.max(0, Math.floor((min - pad) * 10) / 10), Math.ceil((max + pad) * 10) / 10];
  return (
    <figure>
      <figcaption className="mb-1 flex items-baseline justify-between gap-2">
        <span className="font-medium text-slate-900">{param.name}</span>
        <span className="text-xs text-slate-500">{param.unit}{param.reference_range_changed ? " · lab range changed between reports" : ""}</span>
      </figcaption>
      <div className="h-48 w-full" role="img" aria-label={`${param.name} over time: ${data.map((d) => `${d.label} ${d.value}`).join(", ")}`}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            {(lo !== null || hi !== null) && (
              <ReferenceArea y1={lo ?? domain[0]} y2={hi ?? domain[1]} fill="#16a34a" fillOpacity={0.08} stroke="#16a34a" strokeOpacity={0.3}
                label={{ value: "Lab range", position: "insideTopRight", fontSize: 10, fill: "#15803d" }} ifOverflow="extendDomain" />
            )}
            <XAxis dataKey="label" fontSize={11} tickMargin={6} />
            <YAxis domain={domain} fontSize={11} width={48} />
            <Tooltip formatter={(v) => [`${fmtNum(typeof v === "number" ? v : Number(v))} ${param.unit ?? ""}`, param.name]} />
            <Line type="monotone" dataKey="value" stroke="#0f766e" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
}
