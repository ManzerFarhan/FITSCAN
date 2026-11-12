"use client";
import { Input, Select } from "@/components/ui/form";
import { CATEGORY_LABELS, REPORT_CATEGORIES } from "@/lib/constants";

export interface Filters { q: string; category: string; lab: string; from: string; to: string }
export const EMPTY_FILTERS: Filters = { q: "", category: "", lab: "", from: "", to: "" };

export function DocumentFilters({ value, onChange }: { value: Filters; onChange: (f: Filters) => void }) {
  const set = (k: keyof Filters) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => onChange({ ...value, [k]: e.target.value });
  return (
    <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5">
      <Input aria-label="Search" placeholder="Search file or lab..." value={value.q} onChange={set("q")} className="sm:col-span-3 lg:col-span-2" />
      <Select aria-label="Category" value={value.category} onChange={set("category")}>
        <option value="">All categories</option>
        {REPORT_CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_LABELS[c]}</option>)}
      </Select>
      <Input aria-label="From date" type="date" value={value.from} onChange={set("from")} />
      <Input aria-label="To date" type="date" value={value.to} onChange={set("to")} />
    </div>
  );
}
