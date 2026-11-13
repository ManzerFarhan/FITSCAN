"use client";
import { BarChart3, LineChart as LineIcon, PieChart as PieIcon } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ReferenceArea,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/form";
import { CATEGORY_LABELS } from "@/lib/constants";
import type { DashboardCharts as Charts } from "@/lib/types";
import { fmtNum, formatDate } from "@/lib/utils";

// Status colours match the app's badges (within = green, below = sky, above = amber, not compared = slate).
// Every chart also names each status in text (legend / tooltip), so colour is never the only cue.
const STATUS = {
  within: { label: "Within lab range", color: "#16a34a" },
  below: { label: "Below lab range", color: "#0284c7" },
  above: { label: "Above lab range", color: "#d97706" },
  outside: { label: "Outside lab range", color: "#d97706" },
  unknown: { label: "Not compared", color: "#94a3b8" },
} as const;

const AXIS = { fontSize: 11, fill: "#64748b" };
const GRID = "#e2e8f0";

function Empty({ text }: { text: string }) {
  return (
    <div className="flex h-56 flex-col items-center justify-center gap-2 rounded-lg bg-slate-50 text-center text-sm text-slate-500">
      {text}
      <Link href="/analysis" className="font-medium text-brand-700 underline">Upload a lab report</Link>
    </div>
  );
}

/** Donut: how the latest report's values sit against the lab's own ranges. */
function LatestStatusChart({ data }: { data: Charts["latest_status"] }) {
  const rows = data ? (["within", "below", "above", "unknown"] as const)
    .map((k) => ({ key: k, name: STATUS[k].label, value: data[k], color: STATUS[k].color })).filter((r) => r.value > 0) : [];
  const total = rows.reduce((s, r) => s + r.value, 0);
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2"><PieIcon className="h-5 w-5 text-brand-700" aria-hidden />Latest report at a glance</CardTitle>
          <CardDescription>Your values compared with the lab's own ranges.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {!total ? <Empty text="No lab report yet." /> : (
          <div className="flex flex-col items-center gap-4 sm:flex-row lg:flex-col xl:flex-row">
            <div className="relative h-44 w-44 shrink-0" role="img"
              aria-label={`Latest report: ${rows.map((r) => `${r.value} ${r.name.toLowerCase()}`).join(", ")}`}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={rows} dataKey="value" nameKey="name" innerRadius="62%" outerRadius="100%" paddingAngle={rows.length > 1 ? 2 : 0}
                    stroke="#fff" strokeWidth={2} isAnimationActive={false}>
                    {rows.map((r) => <Cell key={r.key} fill={r.color} />)}
                  </Pie>
                  <Tooltip formatter={(v, n) => [`${v} value(s)`, n]} />
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-bold text-slate-900">{total}</span>
                <span className="text-xs text-slate-500">values</span>
              </div>
            </div>
            <ul className="w-full space-y-2 text-sm">
              {rows.map((r) => (
                <li key={r.key} className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-2 text-slate-700">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: r.color }} aria-hidden />{r.name}
                  </span>
                  <span className="font-semibold text-slate-900">{r.value}</span>
                </li>
              ))}
              {data && data.needs_check > 0 && (
                <li className="pt-1 text-xs text-slate-500">{data.needs_check} value(s) not confirmed yet - open the report and press &quot;Confirm all values&quot;.</li>
              )}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/** Stacked bars: latest result of each test, grouped by body system. */
function BySystemChart({ data }: { data: Charts["by_system"] }) {
  const rows = data.map((r) => ({ ...r, name: CATEGORY_LABELS[r.category] ?? r.category }));
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5 text-brand-700" aria-hidden />Results by body system</CardTitle>
          <CardDescription>The latest result of each test you've uploaded, grouped by area.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {!rows.length ? <Empty text="No results yet." /> : (
          <div style={{ height: Math.max(180, rows.length * 44 + 60) }} role="img"
            aria-label={rows.map((r) => `${r.name}: ${r.within} within, ${r.outside} outside, ${r.unknown} not compared`).join("; ")}>
            <ResponsiveContainer>
              <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 8 }} barCategoryGap={10}>
                <CartesianGrid horizontal={false} stroke={GRID} />
                <XAxis type="number" allowDecimals={false} tick={AXIS} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" width={130} tick={{ ...AXIS, fill: "#334155" }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: "#f1f5f9" }} formatter={(v, n) => [`${v} test(s)`, n]} />
                <Bar dataKey="within" name={STATUS.within.label} stackId="s" fill={STATUS.within.color} stroke="#fff" strokeWidth={2} isAnimationActive={false} />
                <Bar dataKey="outside" name={STATUS.outside.label} stackId="s" fill={STATUS.outside.color} stroke="#fff" strokeWidth={2} isAnimationActive={false} />
                <Bar dataKey="unknown" name={STATUS.unknown.label} stackId="s" fill={STATUS.unknown.color} stroke="#fff" strokeWidth={2}
                  radius={[0, 4, 4, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
        {rows.length > 0 && (
          <ul className="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-slate-600" aria-label="Legend">
            {(["within", "outside", "unknown"] as const).map((k) => (
              <li key={k} className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: STATUS[k].color }} aria-hidden />{STATUS[k].label}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

/** One test over time, with the lab's range shaded. Verified values only. */
function TrendsChart({ data }: { data: Charts["trends"] }) {
  const [pid, setPid] = useState<string | null>(null);
  const series = data.find((s) => s.parameter_id === pid) ?? data[0];
  const points = useMemo(() => series?.points.map((p) => ({ ...p, label: formatDate(p.date) })) ?? [], [series]);
  const domain = useMemo<[number, number]>(() => {
    if (!series) return [0, 1];
    const vals = points.map((p) => p.value).concat([series.ref_low, series.ref_high].filter((x): x is number => x !== null));
    const min = Math.min(...vals), max = Math.max(...vals);
    const pad = (max - min || Math.abs(max) || 1) * 0.2;
    // A range with no lower limit (e.g. "< 40") starts at 0, so the shaded band shows the whole range.
    const lo = series.ref_low === null && series.ref_high !== null ? 0 : Math.max(0, Math.floor((min - pad) * 10) / 10);
    return [lo, Math.ceil((max + pad) * 10) / 10];
  }, [points, series]);

  return (
    <Card>
      <CardHeader className="flex-wrap gap-3">
        <div>
          <CardTitle className="flex items-center gap-2"><LineIcon className="h-5 w-5 text-brand-700" aria-hidden />Your values over time</CardTitle>
          <CardDescription>Pick a test to see how its verified values have moved. The shaded band is the lab's range.</CardDescription>
        </div>
        {data.length > 0 && (
          <Select aria-label="Choose a test" className="h-9 w-full sm:w-64" value={series?.parameter_id} onChange={(e) => setPid(e.target.value)}>
            {data.map((s) => <option key={s.parameter_id} value={s.parameter_id}>{s.name} ({s.points.length})</option>)}
          </Select>
        )}
      </CardHeader>
      <CardContent>
        {!series ? <Empty text="Confirm the values of a lab report to see trends." /> : (
          <>
            <div className="h-64 w-full" role="img"
              aria-label={`${series.name} over time: ${points.map((p) => `${p.label} ${fmtNum(p.value)} ${series.unit ?? ""}`).join(", ")}`}>
              <ResponsiveContainer>
                <LineChart data={points} margin={{ top: 12, right: 16, bottom: 0, left: -8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
                  {(series.ref_low !== null || series.ref_high !== null) && (
                    <ReferenceArea y1={series.ref_low ?? domain[0]} y2={series.ref_high ?? domain[1]} fill="#16a34a" fillOpacity={0.08}
                      stroke="#16a34a" strokeOpacity={0.25} ifOverflow="extendDomain"
                      label={{ value: "Lab range", position: "insideTopRight", fontSize: 10, fill: "#15803d" }} />
                  )}
                  <XAxis dataKey="label" tick={AXIS} tickMargin={6} axisLine={{ stroke: GRID }} tickLine={false} />
                  <YAxis domain={domain} tick={AXIS} width={52} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v) => [`${fmtNum(Number(v))} ${series.unit ?? ""}`, series.name]} />
                  <Line type="monotone" dataKey="value" stroke="#0f766e" strokeWidth={2} isAnimationActive={false}
                    dot={{ r: 5, stroke: "#fff", strokeWidth: 2, fill: "#0f766e" }} activeDot={{ r: 7 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {series.points.length < 2 && (
              <p className="mt-2 text-xs text-slate-500">Only one report has this test so far - upload another to see a trend.</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

export function DashboardCharts({ charts }: { charts?: Charts }) {
  const c = charts ?? { latest_status: null, by_system: [], trends: [] };
  return (
    <section aria-label="Charts" className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2"><LatestStatusChart data={c.latest_status} /></div>
        <div className="lg:col-span-3"><BySystemChart data={c.by_system} /></div>
      </div>
      <TrendsChart data={c.trends} />
    </section>
  );
}
