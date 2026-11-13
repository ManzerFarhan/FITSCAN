"use client";
import { BookOpen, CheckCircle2, ChevronDown, ChevronRight, Database, ExternalLink, FlaskConical, Search, XCircle } from "lucide-react";
import { Fragment, useMemo, useState } from "react";
import { LoadState, PageHeader, StatTile, Table, useAdminData } from "@/components/admin/ui";
import { Badge } from "@/components/ui/badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/form";
import { Alert, Spinner, Tabs } from "@/components/ui/misc";
import { api, ApiError } from "@/lib/api";
import type { AdminDataset, DatasetTest, NameCheck } from "@/lib/types";

type Tab = "tests" | "areas" | "reference" | "knowledge";
const STEP = 60;
const fmt = (n: number | null | undefined) => (n == null ? "-" : Number(n).toLocaleString("en-IN", { maximumFractionDigits: 3 }));

/** Admin "Dataset": everything FITSCAN uses to read and explain reports - so gaps are easy to spot and request. */
export default function AdminDatasetPage() {
  const { data, error, loading } = useAdminData<AdminDataset>("/admin/dataset");
  const [tab, setTab] = useState<Tab>("tests");

  return (
    <>
      <PageHeader title="Dataset - what FITSCAN knows"
        description="The tests FITSCAN can recognise, the reference data behind its sanity checks, and the articles behind its explanations. If something is missing, note its name and ask for it to be added." />
      <LoadState error={error} loading={loading && !data} />
      {data && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile label="Tests recognised" value={data.summary.tests} sub={`${data.summary.core} core + ${data.summary.extended} extended, in ${data.summary.categories} areas`} />
            <StatTile label="Printed names known" value={data.summary.names.toLocaleString("en-IN")} sub="names, abbreviations and spellings labs use" />
            <StatTile label="With population data" value={data.summary.with_reference} sub={`${data.summary.reference_values.toLocaleString("en-IN")} real values (NHANES, UCI)`} />
            <StatTile label="Knowledge articles" value={data.summary.kb_articles} sub={`explain ${data.summary.with_kb} of the tests, with sources`} />
          </div>

          <NameChecker />

          <Card>
            <CardHeader><div><CardTitle className="text-base">Where the data comes from</CardTitle>
              <CardDescription>FITSCAN isn&apos;t trained on patient reports. It reads reports with these four sources.</CardDescription></div></CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              {data.sources.map((s) => (
                <div key={s.name} className="rounded-lg border border-slate-200 p-3 text-sm">
                  <p className="flex items-center gap-2 font-semibold text-slate-900">
                    {s.kind === "knowledge" ? <BookOpen className="h-4 w-4 text-brand-700" /> : s.kind === "reference" ? <Database className="h-4 w-4 text-brand-700" /> : <FlaskConical className="h-4 w-4 text-brand-700" />}
                    {s.name}
                  </p>
                  <p className="mt-1 text-slate-700">{s.what}</p>
                  <p className="mt-1 text-slate-600"><span className="font-medium">Used for:</span> {s.used_for}</p>
                  <p className="mt-1 font-mono text-[11px] text-slate-400">{s.file}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Tabs<Tab> value={tab} onChange={setTab} tabs={[
            { value: "tests", label: `All tests (${data.summary.tests})` }, { value: "areas", label: "Coverage by area" },
            { value: "reference", label: "Population data" }, { value: "knowledge", label: `Knowledge library (${data.summary.kb_articles})` },
          ]} />
          {tab === "tests" && <TestsTable data={data} />}
          {tab === "areas" && <Areas data={data} />}
          {tab === "reference" && <Reference data={data} />}
          {tab === "knowledge" && <Knowledge data={data} />}
        </div>
      )}
    </>
  );
}

function NameChecker() {
  const [name, setName] = useState("");
  const [res, setRes] = useState<NameCheck | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const check = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true); setErr(null);
    try { setRes(await api<NameCheck>(`/admin/dataset/check?name=${encodeURIComponent(name.trim())}`)); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Couldn't check."); }
    finally { setBusy(false); }
  };
  return (
    <Card className="border-brand-200">
      <CardHeader><div><CardTitle className="text-base">Is a test covered?</CardTitle>
        <CardDescription>Type a test name exactly as a lab prints it (e.g. &quot;S. Typhi O&quot;, &quot;HbA1c&quot;, &quot;Pus Cells&quot;).</CardDescription></div></CardHeader>
      <CardContent className="space-y-3">
        <form onSubmit={check} className="flex gap-2">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Printed test name" aria-label="Printed test name" />
          <Button type="submit" disabled={busy}>{busy ? <Spinner /> : <Search className="h-4 w-4" />}Check</Button>
        </form>
        {err && <Alert tone="error">{err}</Alert>}
        {res && (res.recognised ? (
          <p className="flex items-center gap-2 text-sm text-green-800"><CheckCircle2 className="h-4 w-4" />
            &quot;{res.input}&quot; is read as <b>{res.test_name}</b> ({res.category}){res.method === "fuzzy" && `, a close spelling match (${Math.round(res.confidence * 100)}%)`}.</p>
        ) : (
          <p className="flex items-center gap-2 text-sm text-red-800"><XCircle className="h-4 w-4" />
            &quot;{res.input}&quot; is not recognised yet - ask for it to be added (with the report section it appears in).</p>
        ))}
      </CardContent>
    </Card>
  );
}

function TestsTable({ data }: { data: AdminDataset }) {
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");
  const [src, setSrc] = useState("");
  const [ref, setRef] = useState("");
  const [shown, setShown] = useState(STEP);
  const [open, setOpen] = useState<string | null>(null);
  const rows = useMemo(() => {
    const k = q.trim().toLowerCase();
    return data.tests.filter((t) => (!cat || t.category === cat) && (!src || t.source === src)
      && (!ref || (ref === "yes") === (t.reference !== null))
      && (!k || t.name.toLowerCase().includes(k) || t.id.includes(k) || t.synonyms.some((s) => s.includes(k))));
  }, [data.tests, q, cat, src, ref]);

  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div className="flex flex-wrap gap-2">
          <Input className="min-w-[220px] flex-1" value={q} onChange={(e) => { setQ(e.target.value); setShown(STEP); }} placeholder="Search a test or any of its printed names" aria-label="Search tests" />
          <Select aria-label="Area" value={cat} onChange={(e) => { setCat(e.target.value); setShown(STEP); }} className="w-auto">
            <option value="">All areas</option>
            {data.categories.map((c) => <option key={c.category} value={c.category}>{c.label} ({c.tests})</option>)}
          </Select>
          <Select aria-label="Source" value={src} onChange={(e) => { setSrc(e.target.value); setShown(STEP); }} className="w-auto">
            <option value="">Core + extended</option><option value="core">Core only</option><option value="extended">Extended only</option>
          </Select>
          <Select aria-label="Population data" value={ref} onChange={(e) => { setRef(e.target.value); setShown(STEP); }} className="w-auto">
            <option value="">Any population data</option><option value="yes">Has population data</option><option value="no">No population data</option>
          </Select>
        </div>
        <p className="text-xs text-slate-500">{rows.length} test{rows.length === 1 ? "" : "s"}. Click a row for every printed name, the sanity range and population figures.</p>
        <Table head={<tr><th className="py-2 pr-3">Test</th><th className="pr-3">Area</th><th className="pr-3">Unit</th>
          <th className="pr-3">Printed names</th><th className="pr-3">Population data</th><th>Articles</th></tr>}>
          {rows.slice(0, shown).map((t) => (
            <Fragment key={t.id}>
              <tr onClick={() => setOpen(open === t.id ? null : t.id)} className="cursor-pointer hover:bg-slate-50">
                <td className="py-2 pr-3">
                  <span className="flex items-center gap-1 font-medium text-slate-900">
                    {open === t.id ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}{t.name}
                  </span>
                  {t.source === "extended" && <Badge className="ml-5 mt-0.5 border-slate-200 bg-slate-50 text-slate-600">extended</Badge>}
                </td>
                <td className="pr-3">{t.category_label}</td>
                <td className="pr-3">{t.unit ?? <span className="text-slate-400">varies by lab</span>}</td>
                <td className="pr-3 text-slate-600">{t.synonyms.slice(0, 3).join(", ")}{t.synonyms.length > 3 && ` +${t.synonyms.length - 3}`}</td>
                <td className="pr-3">{t.reference ? <span className="text-green-800">Yes · {fmt(t.reference.n)} values</span> : <span className="text-slate-400">-</span>}</td>
                <td>{t.kb_articles || <span className="text-slate-400">-</span>}</td>
              </tr>
              {open === t.id && <tr><td colSpan={6} className="bg-slate-50 p-4"><TestDetail t={t} /></td></tr>}
            </Fragment>
          ))}
          {!rows.length && <tr><td colSpan={6} className="py-6 text-center text-slate-500">No test matches - it may be missing from the dataset.</td></tr>}
        </Table>
        {rows.length > shown && <div className="text-center"><Button variant="secondary" size="sm" onClick={() => setShown((n) => n + STEP)}>Show more ({rows.length - shown} left)</Button></div>}
      </CardContent>
    </Card>
  );
}

function TestDetail({ t }: { t: DatasetTest }) {
  return (
    <div className="grid gap-4 text-sm md:grid-cols-2">
      <div className="space-y-2">
        {t.about && <p><span className="text-slate-500">What it measures:</span> {t.about}</p>}
        <p><span className="text-slate-500">Internal id:</span> <code>{t.id}</code></p>
        <p><span className="text-slate-500">Sanity range (catches reading slips, not &quot;normal&quot;):</span>{" "}
          {t.plausible_min != null && t.plausible_max != null ? `${fmt(t.plausible_min)} - ${fmt(t.plausible_max)} ${t.unit ?? ""}` : "none (text result, or units vary between labs)"}</p>
        {t.reference && (
          <p><span className="text-slate-500">Population ({fmt(t.reference.n)} values, {t.reference.sources.join("; ")}):</span>{" "}
            middle 95% {fmt(t.reference.p2_5)} - {fmt(t.reference.p97_5)}, median {fmt(t.reference.p50)} {t.reference.unit ?? ""}</p>
        )}
      </div>
      <div>
        <p className="mb-1 text-slate-500">All printed names recognised ({t.synonyms.length + 1}):</p>
        <div className="flex flex-wrap gap-1">
          {[t.name, ...t.synonyms].map((s) => <span key={s} className="rounded bg-white px-1.5 py-0.5 text-xs ring-1 ring-slate-200">{s}</span>)}
        </div>
      </div>
    </div>
  );
}

function Areas({ data }: { data: AdminDataset }) {
  const max = Math.max(...data.categories.map((c) => c.tests));
  const byCat = (c: string) => data.tests.filter((t) => t.category === c);
  return (
    <Card>
      <CardContent className="p-4">
        <Table head={<tr><th className="py-2 pr-3">Area</th><th className="w-1/2 pr-3">Tests</th><th className="pr-3 text-right">With population data</th><th className="text-right">With articles</th></tr>}>
          {data.categories.map((c) => {
            const ts = byCat(c.category);
            return (
              <tr key={c.category}>
                <td className="py-2 pr-3 font-medium text-slate-900">{c.label}</td>
                <td className="pr-3">
                  <div className="flex items-center gap-2" title={`${c.tests} tests`}>
                    <div className="h-2.5 rounded-r bg-brand-600" style={{ width: `${(c.tests / max) * 100}%`, minWidth: 4 }} />
                    <span className="tabular-nums text-slate-700">{c.tests}</span>
                  </div>
                </td>
                <td className="pr-3 text-right tabular-nums">{ts.filter((t) => t.reference).length}</td>
                <td className="text-right tabular-nums">{ts.filter((t) => t.kb_articles).length}</td>
              </tr>
            );
          })}
        </Table>
      </CardContent>
    </Card>
  );
}

function Reference({ data }: { data: AdminDataset }) {
  return (
    <Card>
      <CardHeader><div><CardTitle className="text-base">Population reference data</CardTitle>
        <CardDescription>Summary statistics only (percentiles) - no individual records are stored. Used to catch reading slips, never as normal ranges or for diagnosis; the lab&apos;s own printed range always decides High/Low.</CardDescription></div></CardHeader>
      <CardContent>
        <Table head={<tr><th className="py-2 pr-3">Source</th><th className="pr-3 text-right">Tests covered</th><th className="text-right">Values summarised</th></tr>}>
          {data.reference_sources.map((s) => (
            <tr key={s.source}><td className="py-2 pr-3">{s.source}</td><td className="pr-3 text-right tabular-nums">{s.tests}</td><td className="text-right tabular-nums">{s.values.toLocaleString("en-IN")}</td></tr>
          ))}
        </Table>
      </CardContent>
    </Card>
  );
}

function Knowledge({ data }: { data: AdminDataset }) {
  const [q, setQ] = useState("");
  const k = q.trim().toLowerCase();
  const rows = data.knowledge.filter((d) => !k || d.title.toLowerCase().includes(k) || d.tests.some((t) => t.toLowerCase().includes(k)));
  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search articles or tests" aria-label="Search articles" />
        <Table head={<tr><th className="py-2 pr-3">Article</th><th className="pr-3">Source</th><th>Explains</th></tr>}>
          {rows.map((d) => (
            <tr key={d.title + d.url} className="align-top">
              <td className="py-2 pr-3"><a href={d.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-medium text-brand-700 hover:underline">{d.title}<ExternalLink className="h-3 w-3" /></a></td>
              <td className="pr-3 pt-2">{d.source}</td>
              <td className="pt-2 text-slate-600">{d.tests.join(", ") || "General"}</td>
            </tr>
          ))}
        </Table>
      </CardContent>
    </Card>
  );
}
