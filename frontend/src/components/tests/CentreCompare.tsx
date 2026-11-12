import { VerifiedBadge } from "@/components/ui/badges";
import type { RankedCentre } from "@/lib/types";

const ROWS: { label: string; get: (r: RankedCentre) => React.ReactNode }[] = [
  { label: "Listing", get: (r) => <VerifiedBadge verified={r.verified} note={r.verification_note} /> },
  { label: "Distance", get: (r) => (r.distance_km !== null ? `${r.distance_km} km` : "-") },
  { label: "Rating", get: (r) => (r.centre.rating !== null ? `${r.centre.rating} (${r.centre.rating_count ?? 0})` : "-") },
  { label: "Phone", get: (r) => r.centre.phone ?? "-" },
  { label: "Website", get: (r) => (r.centre.website ? "Yes" : "-") },
  { label: "Opening hours", get: (r) => (r.centre.hours.length ? "Listed" : "-") },
  { label: "Test availability", get: (r) => r.test_availability },
  { label: "Price", get: (r) => r.centre.price ?? "Not listed" },
  { label: "Match score", get: (r) => `${Math.round(r.score * 100)}%` },
];

/** FR-TEST-9: side-by-side for 2-3 centres. */
export function CentreCompare({ items }: { items: RankedCentre[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[480px] text-sm">
        <thead>
          <tr><th className="w-36 p-2 text-left text-slate-500" />{items.map((r) => <th key={r.centre.provider_id} className="p-2 text-left font-semibold text-slate-900">{r.centre.name}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {ROWS.map((row) => (
            <tr key={row.label}><td className="p-2 text-slate-500">{row.label}</td>{items.map((r) => <td key={r.centre.provider_id} className="p-2">{row.get(r)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
