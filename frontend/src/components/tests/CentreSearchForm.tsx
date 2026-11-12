"use client";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Field, Select } from "@/components/ui/form";
import { Spinner } from "@/components/ui/misc";
import { LocationPicker, type LocationValue } from "./LocationPicker";

/** FR-TEST-4: test(s), city, locality, postal code, distance. */
export function CentreSearchForm({ location, onLocation, source, radius, onRadius, searchLabel, busy, onSearch }: {
  location: LocationValue; onLocation: (v: LocationValue) => void; source: string | null;
  radius: number; onRadius: (r: number) => void; searchLabel: string; busy: boolean; onSearch: () => void;
}) {
  return (
    <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); onSearch(); }}>
      <LocationPicker value={location} onChange={onLocation} source={source} />
      <div className="flex flex-wrap items-end gap-3">
        <div className="w-40">
          <Field label="Distance" htmlFor="radius">
            <Select id="radius" value={radius} onChange={(e) => onRadius(Number(e.target.value))}>
              {[2, 5, 10, 20, 40].map((r) => <option key={r} value={r}>Within {r} km</option>)}
            </Select>
          </Field>
        </div>
        <Button type="submit" disabled={busy || (!location.city && !location.locality && !location.postal_code && location.lat === undefined)}>
          {busy ? <Spinner /> : <Search className="h-4 w-4" />}Find centres{searchLabel ? ` for ${searchLabel}` : ""}
        </Button>
      </div>
    </form>
  );
}
