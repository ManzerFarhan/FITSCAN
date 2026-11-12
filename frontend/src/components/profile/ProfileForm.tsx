"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/form";
import { Alert, Spinner } from "@/components/ui/misc";
import { api, ApiError } from "@/lib/api";
import { BMI_CATEGORY_LABEL, bmiFrom } from "@/lib/constants";
import type { User } from "@/lib/types";

/** FR-PROF-1. Gender is optional - used only to pick sex-specific lab ranges, never guessed. */
export function ProfileForm({ user, onSaved, fields = "all" }: { user: User; onSaved: (u: User) => void; fields?: "all" | "location" }) {
  const [f, setF] = useState({
    full_name: user.full_name ?? "", phone: user.phone ?? "", dob: user.dob ?? "", gender: user.gender ?? "",
    preferred_city: user.preferred_city ?? "", address: user.address ?? "",
    height_cm: user.height_cm ? String(user.height_cm) : "", weight_kg: user.weight_kg ? String(user.weight_kg) : "",
  });
  const h = Number(f.height_cm), w = Number(f.weight_kg);
  const bmi = h >= 50 && h <= 250 && w >= 10 && w <= 350 ? bmiFrom(h, w) : null;
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setF({ ...f, [k]: e.target.value });

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setMsg(null);
    const body: Record<string, string | number | null> = Object.fromEntries(Object.entries(f).map(([k, v]) => [k, v === "" ? null : v]));
    for (const k of ["height_cm", "weight_kg"] as const) body[k] = f[k] === "" ? null : Number(f[k]);  // optional, for BMI
    try {
      onSaved(await api<User>("/profile", { method: "PATCH", json: fields === "location" ? { preferred_city: body.preferred_city, address: body.address } : body }));
      setMsg({ tone: "success", text: "Saved." });
    } catch (err) {
      setMsg({ tone: "error", text: err instanceof ApiError ? err.message : "Could not save." });
    } finally { setBusy(false); }
  };

  return (
    <form onSubmit={save} className="space-y-4">
      {fields === "all" && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Full name" htmlFor="p-name"><Input id="p-name" value={f.full_name} onChange={set("full_name")} autoComplete="name" /></Field>
          <Field label="Email" htmlFor="p-email" hint="Change it under Account"><Input id="p-email" value={user.email} disabled /></Field>
          <Field label="Phone" htmlFor="p-phone"><Input id="p-phone" value={f.phone} onChange={set("phone")} inputMode="tel" autoComplete="tel" /></Field>
          <Field label="Date of birth" htmlFor="p-dob"><Input id="p-dob" type="date" value={f.dob} onChange={set("dob")} max={new Date().toISOString().slice(0, 10)} /></Field>
          <Field label="Gender (optional)" htmlFor="p-gender" hint="Helps apply sex-specific ranges printed on your reports.">
            <Select id="p-gender" value={f.gender} onChange={set("gender")}>
              <option value="">Prefer not to say</option><option value="Female">Female</option><option value="Male">Male</option><option value="Other">Other</option>
            </Select>
          </Field>
          <Field label="Height in cm (optional)" htmlFor="p-height" hint="Used only to show your BMI.">
            <Input id="p-height" type="number" inputMode="decimal" step="0.1" min={50} max={250} value={f.height_cm} onChange={set("height_cm")} placeholder="e.g. 170" />
          </Field>
          <Field label="Weight in kg (optional)" htmlFor="p-weight" hint="Leave both empty to hide BMI.">
            <Input id="p-weight" type="number" inputMode="decimal" step="0.1" min={10} max={350} value={f.weight_kg} onChange={set("weight_kg")} placeholder="e.g. 65" />
          </Field>
          {bmi && (
            <p className="rounded-lg bg-brand-50 p-3 text-sm text-slate-700 sm:col-span-2" aria-live="polite">
              Your BMI: <strong className="text-slate-900">{bmi.value.toFixed(1)}</strong> - {BMI_CATEGORY_LABEL[bmi.category]}. It also shows on your dashboard.
            </p>
          )}
        </div>
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Preferred city" htmlFor="p-city" hint="Used first when searching for diagnostic centres.">
          <Input id="p-city" value={f.preferred_city} onChange={set("preferred_city")} autoComplete="address-level2" />
        </Field>
        <Field label="Address (optional)" htmlFor="p-addr"><Textarea id="p-addr" value={f.address} onChange={set("address")} rows={2} autoComplete="street-address" /></Field>
      </div>
      {msg && <Alert tone={msg.tone}>{msg.text}</Alert>}
      <Button type="submit" disabled={busy}>{busy && <Spinner />}Save</Button>
    </form>
  );
}
