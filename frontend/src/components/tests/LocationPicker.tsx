"use client";
import { LocateFixed } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/form";

export interface LocationValue { city: string; locality: string; postal_code: string; lat?: number; lng?: number }

const SOURCE_LABEL: Record<string, string> = {
  PROFILE: "from your profile's preferred city",
  DOCUMENT_PATIENT_ADDRESS: "from the patient address on your report",
  MANUAL: "entered by you",
};

/** FR-TEST-3 / BR-06: profile city -> patient address from document -> manual. Never the lab's address. */
export function LocationPicker({ value, onChange, source }: { value: LocationValue; onChange: (v: LocationValue) => void; source: string | null }) {
  const useMine = () => {
    navigator.geolocation?.getCurrentPosition(
      (pos) => onChange({ ...value, lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => alert("Couldn't get your location. Please type your city instead."),
      { timeout: 10000 },
    );
  };
  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="City" htmlFor="loc-city"><Input id="loc-city" value={value.city} placeholder="e.g. Pune" onChange={(e) => onChange({ ...value, city: e.target.value, lat: undefined, lng: undefined })} /></Field>
        <Field label="Area / locality" htmlFor="loc-loc"><Input id="loc-loc" value={value.locality} placeholder="e.g. Kothrud" onChange={(e) => onChange({ ...value, locality: e.target.value, lat: undefined, lng: undefined })} /></Field>
        <Field label="PIN code" htmlFor="loc-pin"><Input id="loc-pin" value={value.postal_code} inputMode="numeric" maxLength={6} onChange={(e) => onChange({ ...value, postal_code: e.target.value, lat: undefined, lng: undefined })} /></Field>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
        <span>
          {value.lat !== undefined ? "Using your current location." : source ? `Location ${SOURCE_LABEL[source] ?? ""} - you can change it.` : "We never use the lab's address as your location."}
        </span>
        <Button type="button" variant="ghost" size="sm" onClick={useMine}><LocateFixed className="h-4 w-4" />Use my location</Button>
      </div>
    </div>
  );
}
