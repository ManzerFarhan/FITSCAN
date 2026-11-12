"use client";
import { Check, Plus, X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/form";
import { cn } from "@/lib/utils";

export const COMMON_TESTS = [
  "Complete Blood Count", "Lipid Profile", "Thyroid Profile", "HbA1c", "Blood Sugar (Fasting)",
  "Liver Function Test", "Kidney Function Test", "Vitamin D", "Vitamin B12", "Iron Studies",
];

/** The user chooses which test(s) to search for - suggestions are never applied without a tap. */
export function TestPicker({ value, onChange, fromReport }: { value: string[]; onChange: (v: string[]) => void; fromReport: string[] }) {
  const [custom, setCustom] = useState("");
  const toggle = (t: string) => onChange(value.includes(t) ? value.filter((x) => x !== t) : [...value, t].slice(0, 10));
  const add = () => {
    const t = custom.trim();
    if (t && !value.includes(t)) onChange([...value, t].slice(0, 10));
    setCustom("");
  };
  const extras = value.filter((t) => !fromReport.includes(t) && !COMMON_TESTS.includes(t));

  const chip = (t: string) => {
    const on = value.includes(t);
    return (
      <button key={t} type="button" onClick={() => toggle(t)} aria-pressed={on}
        className={cn("inline-flex items-center gap-1 rounded-full border px-3 py-1.5 text-sm transition",
          on ? "border-brand-600 bg-brand-50 text-brand-800" : "border-slate-300 text-slate-700 hover:bg-slate-50")}>
        {on && <Check className="h-3.5 w-3.5" aria-hidden />}{t}
      </button>
    );
  };

  return (
    <div className="space-y-4">
      {fromReport.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">From your lab report</p>
          <div className="flex flex-wrap gap-2">{fromReport.map(chip)}</div>
        </div>
      )}
      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Common tests</p>
        <div className="flex flex-wrap gap-2">{COMMON_TESTS.filter((t) => !fromReport.includes(t)).map(chip)}</div>
      </div>
      {extras.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {extras.map((t) => (
            <span key={t} className="inline-flex items-center gap-1 rounded-full border border-brand-600 bg-brand-50 px-3 py-1.5 text-sm text-brand-800">
              {t}<button type="button" aria-label={`Remove ${t}`} onClick={() => toggle(t)}><X className="h-3.5 w-3.5" /></button>
            </span>
          ))}
        </div>
      )}
      <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); add(); }}>
        <Input aria-label="Another test" placeholder="Another test, e.g. Urine Routine" value={custom} maxLength={80} onChange={(e) => setCustom(e.target.value)} />
        <Button type="submit" variant="secondary" disabled={!custom.trim()}><Plus className="h-4 w-4" />Add</Button>
      </form>
      <p className="text-xs text-slate-500">
        {value.length ? `${value.length} test(s) selected.` : "No test selected - we'll show any diagnostic centre nearby."}
      </p>
    </div>
  );
}
