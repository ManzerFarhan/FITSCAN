import { Clock, ExternalLink, Globe, MapPin, Navigation, Phone, Star, Stethoscope } from "lucide-react";
import { VerifiedBadge } from "@/components/ui/badges";
import type { RankedCentre } from "@/lib/types";
import { cn } from "@/lib/utils";

export function directionsUrl(lat: number, lng: number) {
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
}

/** FR-TEST-6/7. Price is shown only when reliably sourced (never invented). */
export function CentreCard({ r, rank, active, compare, onCompare, onFocus }: {
  r: RankedCentre; rank: number; active?: boolean; compare: boolean; onCompare: (on: boolean) => void; onFocus: () => void;
}) {
  const c = r.centre;
  return (
    <article onMouseEnter={onFocus} className={cn("rounded-xl border bg-white p-4 shadow-sm transition", active ? "border-brand-500 ring-2 ring-brand-100" : "border-slate-200")}>
      <div className="flex items-start gap-3">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-700 text-sm font-bold text-white">{rank}</span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-slate-900">{c.name}</h3>
            {c.kind === "doctor" && <span className="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-800"><Stethoscope className="h-3 w-3" aria-hidden />Doctor</span>}
            <VerifiedBadge verified={r.verified} note={r.verification_note} />
          </div>
          <p className="mt-0.5 flex items-start gap-1 text-sm text-slate-600"><MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" />{c.address ?? ([c.locality, c.city].filter(Boolean).join(", ") || "Address not listed")}</p>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600">
            {r.distance_km !== null && <span>{r.distance_km} km away</span>}
            {c.rating !== null && <span className="inline-flex items-center gap-1"><Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />{c.rating} ({c.rating_count ?? 0} reviews)</span>}
            {c.phone && <a href={`tel:${c.phone}`} className="inline-flex items-center gap-1 text-brand-700 hover:underline"><Phone className="h-3.5 w-3.5" />{c.phone}</a>}
            {c.website && <a href={c.website} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-700 hover:underline"><Globe className="h-3.5 w-3.5" />Website</a>}
          </div>
          {c.hours.length > 0 && (
            <details className="mt-1 text-sm text-slate-600">
              <summary className="inline-flex cursor-pointer items-center gap-1"><Clock className="h-3.5 w-3.5" />Opening hours</summary>
              <ul className="mt-1 pl-5 text-xs">{c.hours.map((h) => <li key={h}>{h}</li>)}</ul>
            </details>
          )}
          <p className="mt-2 text-xs text-slate-500">{c.kind === "doctor" ? "Doctor" : "Test availability"}: {r.test_availability}{c.price ? ` · Price: ${c.price}` : " · Price: not listed"}</p>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
            <a href={directionsUrl(c.lat, c.lng)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-medium text-brand-700 hover:underline"><Navigation className="h-3.5 w-3.5" />Directions</a>
            {c.maps_url && <a href={c.maps_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-slate-600 hover:underline"><ExternalLink className="h-3.5 w-3.5" />Open in Google Maps</a>}
            {c.booking_url && <a href={c.booking_url} target="_blank" rel="noreferrer" className="text-slate-600 hover:underline">Book</a>}
            <label className="ml-auto flex items-center gap-1.5 text-slate-600">
              <input type="checkbox" className="h-4 w-4 accent-brand-700" checked={compare} onChange={(e) => onCompare(e.target.checked)} />Compare
            </label>
          </div>
        </div>
      </div>
    </article>
  );
}
