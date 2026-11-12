"use client";
import { Pencil, Scale, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { LoginToUnlock } from "@/components/layout/LoginToUnlock";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input } from "@/components/ui/form";
import { Alert, Spinner } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { BMI_CATEGORY_LABEL, bmiFrom, type BmiCategory } from "@/lib/constants";
import type { User } from "@/lib/types";

const SCALE = { min: 15, max: 40 };
const BANDS: { cat: BmiCategory; from: number; to: number; color: string }[] = [
  { cat: "UNDERWEIGHT", from: 15, to: 18.5, color: "#0284c7" },
  { cat: "NORMAL", from: 18.5, to: 25, color: "#16a34a" },
  { cat: "OVERWEIGHT", from: 25, to: 30, color: "#d97706" },
  { cat: "OBESE", from: 30, to: 40, color: "#dc2626" },
];
const pct = (v: number) => ((Math.min(Math.max(v, SCALE.min), SCALE.max) - SCALE.min) / (SCALE.max - SCALE.min)) * 100;

type Hw = { height_cm: number; weight_kg: number };

export function BmiCard() {
  const { user, loading, setUser } = useAuth();
  const [hw, setHw] = useState<Hw | null>(null);
  const [editing, setEditing] = useState(false);
  const [unit, setUnit] = useState<"cm" | "ft">("cm");
  const [form, setForm] = useState({ cm: "", ft: "", inch: "", kg: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading) return;
    setHw(user?.height_cm && user.weight_kg ? { height_cm: user.height_cm, weight_kg: user.weight_kg } : null);
  }, [user, loading]);

  const startEdit = () => {
    setForm({ cm: hw ? String(hw.height_cm) : "", ft: "", inch: "", kg: hw ? String(hw.weight_kg) : "" });
    setError(null); setEditing(true);
  };

  const persist = async (next: Hw | null) => {
    setUser(await api<User>("/profile", { method: "PATCH", json: { height_cm: next?.height_cm ?? null, weight_kg: next?.weight_kg ?? null } }));
    setHw(next);
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    const height = unit === "cm" ? Number(form.cm) : (Number(form.ft) * 12 + Number(form.inch || 0)) * 2.54;
    const weight = Number(form.kg);
    if (!(height >= 50 && height <= 250)) return setError("Enter a height between 50 and 250 cm (about 1 ft 8 in to 8 ft 2 in).");
    if (!(weight >= 10 && weight <= 350)) return setError("Enter a weight between 10 and 350 kg.");
    setBusy(true); setError(null);
    try {
      await persist({ height_cm: Math.round(height * 10) / 10, weight_kg: Math.round(weight * 10) / 10 });
      setEditing(false);
    } catch { setError("Couldn't save. Please try again."); } finally { setBusy(false); }
  };

  const remove = async () => {
    setBusy(true);
    try { await persist(null); setEditing(false); } catch { setError("Couldn't remove. Please try again."); } finally { setBusy(false); }
  };

  const result = hw ? bmiFrom(hw.height_cm, hw.weight_kg) : null;
  const band = result ? BANDS.find((b) => b.cat === result.category)! : null;

  return (
    <Card aria-labelledby="bmi-title">
      <CardHeader>
        <div>
          <CardTitle id="bmi-title" className="flex items-center gap-2"><Scale className="h-5 w-5 text-brand-700" aria-hidden />Body Mass Index (BMI)<span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-normal text-slate-500">Optional</span></CardTitle>
          <CardDescription>{user ? "Saved to your profile. You can change or remove it any time." : "Available with a free account."}</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {!loading && !user ? (
          <LoginToUnlock feature="BMI" compact description="Add your height and weight once and see your BMI on the dashboard. You can also set them in Profile." />
        ) : editing || !result ? (
          <form onSubmit={save} className="space-y-3" aria-label="BMI details">
            {!result && !editing && <p className="text-sm text-slate-600">Add your height and weight to see your BMI on the dashboard.</p>}
            <div className="flex items-center gap-2 text-xs" role="group" aria-label="Height unit">
              <span className="text-slate-500">Height in</span>
              {(["cm", "ft"] as const).map((u) => (
                <button key={u} type="button" aria-pressed={unit === u} onClick={() => setUnit(u)}
                  className={`rounded-full border px-2.5 py-0.5 ${unit === u ? "border-brand-700 bg-brand-50 font-medium text-brand-800" : "border-slate-300 text-slate-600"}`}>
                  {u === "cm" ? "cm" : "feet & inches"}
                </button>
              ))}
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {unit === "cm" ? (
                <Field label="Height (cm)" htmlFor="bmi-cm"><Input id="bmi-cm" type="number" inputMode="decimal" step="0.1" min={50} max={250} required value={form.cm} onChange={(e) => setForm({ ...form, cm: e.target.value })} placeholder="e.g. 170" /></Field>
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Feet" htmlFor="bmi-ft"><Input id="bmi-ft" type="number" inputMode="numeric" min={1} max={8} required value={form.ft} onChange={(e) => setForm({ ...form, ft: e.target.value })} placeholder="5" /></Field>
                  <Field label="Inches" htmlFor="bmi-in"><Input id="bmi-in" type="number" inputMode="decimal" min={0} max={11.9} step="0.1" value={form.inch} onChange={(e) => setForm({ ...form, inch: e.target.value })} placeholder="7" /></Field>
                </div>
              )}
              <Field label="Weight (kg)" htmlFor="bmi-kg"><Input id="bmi-kg" type="number" inputMode="decimal" step="0.1" min={10} max={350} required value={form.kg} onChange={(e) => setForm({ ...form, kg: e.target.value })} placeholder="e.g. 65" /></Field>
            </div>
            {error && <Alert tone="error">{error}</Alert>}
            <div className="flex gap-2">
              <Button type="submit" disabled={busy}>{busy && <Spinner />}Calculate BMI</Button>
              {editing && <Button type="button" variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>}
            </div>
          </form>
        ) : (
          <>
            <div className="flex flex-wrap items-end gap-x-4 gap-y-1">
              <p className="leading-none"><span className="text-5xl font-bold tabular-nums text-slate-900">{result.value.toFixed(1)}</span><span className="text-lg text-slate-500"> kg/m²</span></p>
              <p className="flex items-center gap-1.5 pb-1 text-sm font-medium text-slate-700">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: band!.color }} aria-hidden />{BMI_CATEGORY_LABEL[result.category]}
              </p>
            </div>
            <div>
              <div className="relative pt-3" role="img" aria-label={`BMI ${result.value}, ${BMI_CATEGORY_LABEL[result.category]}`}>
                <div className="absolute top-0 -translate-x-1/2 text-[10px] leading-none text-slate-900" style={{ left: `${pct(result.value)}%` }} aria-hidden>▼</div>
                <div className="flex h-2.5 gap-0.5 overflow-hidden rounded-full">
                  {BANDS.map((b) => <div key={b.cat} style={{ width: `${pct(b.to) - pct(b.from)}%`, background: b.color }} />)}
                </div>
              </div>
              <div className="relative mt-1 h-4 text-[10px] text-slate-500" aria-hidden>
                {[18.5, 25, 30].map((t) => <span key={t} className="absolute -translate-x-1/2 tabular-nums" style={{ left: `${pct(t)}%` }}>{t}</span>)}
              </div>
              <ul className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600">
                {BANDS.map((b) => <li key={b.cat} className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: b.color }} aria-hidden />{BMI_CATEGORY_LABEL[b.cat]}</li>)}
              </ul>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-slate-600">
              <span>Height {hw!.height_cm} cm · Weight {hw!.weight_kg} kg</span>
              <span className="flex gap-1">
                <Button size="sm" variant="secondary" onClick={startEdit}><Pencil className="h-3.5 w-3.5" aria-hidden />Update</Button>
                <Button size="sm" variant="ghost" onClick={remove} disabled={busy} aria-label="Remove BMI"><Trash2 className="h-3.5 w-3.5" aria-hidden />Remove</Button>
              </span>
            </div>
            {error && <Alert tone="error">{error}</Alert>}
          </>
        )}
        <p className="text-xs text-slate-500">
          BMI is a general screening measure for adults; it does not measure body fat or health directly. For South Asian adults, health
          risks may begin at a lower BMI (around 23). Talk to your doctor about what is right for you.
        </p>
      </CardContent>
    </Card>
  );
}
