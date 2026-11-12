"use client";
import { ArrowLeft, ExternalLink } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { CentreCard } from "@/components/tests/CentreCard";
import { CentreCompare } from "@/components/tests/CentreCompare";
import { CentreSearchForm } from "@/components/tests/CentreSearchForm";
import { LoginToUnlock } from "@/components/layout/LoginToUnlock";
import type { LocationValue } from "@/components/tests/LocationPicker";
import { TestPicker } from "@/components/tests/TestPicker";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Select } from "@/components/ui/form";
import { Alert, Dialog, Skeleton } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import { DOCTOR_TYPE_LABEL, DOCTOR_TYPES, type DoctorType } from "@/lib/constants";
import type { CentreSearchResult, ExtractionOut, LocationOut } from "@/lib/types";

const CentreMap = dynamic(() => import("@/components/tests/CentreMap"), { ssr: false, loading: () => <Skeleton className="h-[420px]" /> });

// Report category -> the test name people book at a centre.
const CATEGORY_TEST: Record<string, string> = {
  CBC: "Complete Blood Count", LFT: "Liver Function Test", KFT: "Kidney Function Test", LIPID: "Lipid Profile",
  THYROID: "Thyroid Profile", SUGAR: "HbA1c", B12: "Vitamin B12", VITAMIN_D: "Vitamin D",
  IRON: "Iron Studies", COAG: "Coagulation Profile (PT/INR)", CARDIAC: "Cardiac Markers", HORMONE: "Hormone Panel",
  INFLAMMATION: "C-Reactive Protein (CRP)",
};

function TestsInner() {
  const docId = useSearchParams().get("doc");
  const [testNames, setTestNames] = useState<string[]>([]);
  const [doctorType, setDoctorType] = useState<DoctorType | "">("");
  const [fromReport, setFromReport] = useState<string[]>([]);
  const [reportName, setReportName] = useState<string | null>(null);
  const [location, setLocation] = useState<LocationValue>({ city: "", locality: "", postal_code: "" });
  const [locSource, setLocSource] = useState<string | null>(null);
  const [radius, setRadius] = useState(10);
  const [result, setResult] = useState<CentreSearchResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [showCompare, setShowCompare] = useState(false);

  useEffect(() => {
    api<LocationOut>("/centres/location").then((l) => {
      setLocation({ city: l.city ?? "", locality: l.locality ?? "", postal_code: l.postal_code ?? "" });
      setLocSource(l.source);
    }).catch(() => undefined);
  }, []);

  // Coming from an analysed report: suggest its panel plus the verified values outside the lab's range.
  useEffect(() => {
    if (!docId) return;
    api<ExtractionOut>(`/documents/${docId}/extraction`).then((ex) => {
      const names = new Set<string>();
      const cat = ex.document.report_category;
      if (cat && CATEGORY_TEST[cat]) names.add(CATEGORY_TEST[cat]);
      ex.parameters.filter((p) => p.verified && (p.status === "ABOVE" || p.status === "BELOW"))
        .forEach((p) => names.add(p.canonical_name ?? p.name_raw));
      const list = [...names].slice(0, 8);
      setFromReport(list);
      setReportName(ex.document.original_filename);
      if (cat && CATEGORY_TEST[cat]) setTestNames([CATEGORY_TEST[cat]]);
    }).catch(() => undefined);
  }, [docId]);

  const search = async () => {
    setBusy(true); setError(null); setCompareIds([]);
    try {
      const res = await api<CentreSearchResult>("/centres/search", {
        method: "POST",
        json: {
          test_names: testNames, doctor_type: doctorType || null, radius_km: radius,
          city: location.city || null, locality: location.locality || null, postal_code: location.postal_code || null,
          lat: location.lat ?? null, lng: location.lng ?? null,
        },
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Search failed.");
    } finally { setBusy(false); }
  };

  const searchLabel = [testNames.length ? `${testNames.length} test(s)` : "", doctorType ? DOCTOR_TYPE_LABEL[doctorType] : ""]
    .filter(Boolean).join(" + ");
  const resultDoctor = result?.doctor_type ? DOCTOR_TYPE_LABEL[result.doctor_type] : null;
  const wanted = [...(result?.tests ?? []), ...(resultDoctor ? [resultDoctor] : [])];
  const mapsQuery = result?.tests[0] ? `${result.tests[0]} lab` : resultDoctor ? resultDoctor.replace(/ \(.*\)$/, "") : "diagnostic centre lab";
  const compared = useMemo(() => result?.results.filter((r) => compareIds.includes(r.centre.provider_id)) ?? [], [result, compareIds]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tests & Diagnostic Centres</h1>
          <p className="text-slate-600">Choose the test you need - and, if you like, a type of doctor - and find places near you.</p>
        </div>
        <Link href={docId ? `/analysis?doc=${docId}` : "/analysis"} className={buttonVariants({ variant: "secondary" })}>
          <ArrowLeft className="h-4 w-4" />{docId ? "Back to my analysis" : "Upload & Analysis"}
        </Link>
      </div>
      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Which test do you need?</CardTitle>
              <CardDescription>{reportName ? `Suggestions from ${reportName}. Tap to choose.` : "Tap to choose, or type your own."}</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <TestPicker value={testNames} onChange={setTestNames} fromReport={fromReport} />
            <div className="border-t border-slate-100 pt-5">
              <Field label="Type of doctor (optional)" htmlFor="doctor-type"
                hint={doctorType ? "We'll also show this kind of doctor or clinic near you." : "Leave as is to search for test centres only."}>
                <Select id="doctor-type" value={doctorType} onChange={(e) => setDoctorType(e.target.value as DoctorType | "")}>
                  <option value="">No doctor - test centres only</option>
                  {DOCTOR_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </Select>
              </Field>
            </div>
          </CardContent>
        </Card>
        <Card className="lg:col-span-3">
          <CardHeader><div><CardTitle>Find centres near you</CardTitle><CardDescription>Enter your area or use your current location.</CardDescription></div></CardHeader>
          <CardContent>
            <CentreSearchForm location={location} onLocation={(v) => { setLocation(v); setLocSource("MANUAL"); }} source={locSource}
              radius={radius} onRadius={setRadius} searchLabel={searchLabel} busy={busy} onSearch={search} />
          </CardContent>
        </Card>
      </div>
      {error && <Alert tone="error">{error}</Alert>}
      {result && (
        <section className="space-y-4" aria-label="Search results">
          <Alert tone="warning" title="Please confirm before you go">{result.disclaimer}</Alert>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-slate-600">
              {result.results.length} place(s) within {result.radius_km} km{wanted.length ? ` for ${wanted.join(", ")}` : ""} · data from{" "}
              {result.provider === "google_places" ? "Google Maps" : result.provider === "openstreetmap" ? "OpenStreetMap" : result.provider}
            </p>
            <div className="flex flex-wrap gap-2">
              <a target="_blank" rel="noreferrer" className={buttonVariants({ variant: "secondary", size: "sm" })}
                href={`https://www.google.com/maps/search/${encodeURIComponent(mapsQuery)}/@${result.origin.lat},${result.origin.lng},14z`}>
                <ExternalLink className="h-4 w-4" />See more on Google Maps
              </a>
              <Button variant="secondary" size="sm" disabled={compared.length < 2} onClick={() => setShowCompare(true)}>
                Compare selected ({compared.length}/3)
              </Button>
            </div>
          </div>
          {result.results.length === 0 ? (
            <Alert tone="info">No places found. Try a larger distance, a nearby area, or &quot;See more on Google Maps&quot; above.</Alert>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="order-2 space-y-3 lg:order-1">
                {result.results.map((r, i) => (
                  <CentreCard key={r.centre.provider_id} r={r} rank={i + 1} active={activeId === r.centre.provider_id}
                    compare={compareIds.includes(r.centre.provider_id)} onFocus={() => setActiveId(r.centre.provider_id)}
                    onCompare={(on) => setCompareIds((ids) => on ? [...ids, r.centre.provider_id].slice(-3) : ids.filter((x) => x !== r.centre.provider_id))} />
                ))}
              </div>
              <div className="order-1 lg:order-2">
                <div className="lg:sticky lg:top-20">
                  <CentreMap origin={result.origin} radiusKm={result.radius_km} results={result.results} activeId={activeId} onSelect={setActiveId} />
                  <p className="mt-2 text-xs text-slate-500">Searching near: {result.origin.label ?? "your location"}. Change the location above to search elsewhere.</p>
                </div>
              </div>
            </div>
          )}
        </section>
      )}
      <Dialog open={showCompare} onClose={() => setShowCompare(false)} title="Compare centres" wide>
        <CentreCompare items={compared} />
      </Dialog>
    </div>
  );
}

export default function TestsPage() {
  const { user, loading } = useAuth();
  if (loading) return <Skeleton className="h-64" />;
  if (!user) {  // log in to unlock
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tests & Diagnostic Centres</h1>
          <p className="text-slate-600">Choose the test you need and find diagnostic centres near you.</p>
        </div>
        <LoginToUnlock feature="Tests & Centres"
          description="Pick the tests from your report and see nearby diagnostic centres on a map, with phone numbers and directions." />
      </div>
    );
  }
  return <Suspense fallback={<Skeleton className="h-64" />}><TestsInner /></Suspense>;
}
