"use client";
import {
  ArrowDown, ArrowRight, Bot, BrainCircuit, CheckCircle2, Cloud, Code2, Database, FileSearch, FileText, GitBranch,
  Globe, Image as ImageIcon, ListChecks, Mail, MapPin, MonitorSmartphone, Ruler, ScanText, Server, ShieldCheck,
  Sparkles, TableProperties, TestTube2, UserCheck,
} from "lucide-react";
import { LoadState, PageHeader, useAdminData } from "@/components/admin/ui";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { AdminSystem } from "@/lib/types";
import { cn } from "@/lib/utils";

type Icon = typeof Server;

/** Admin "System": live status, how the pieces fit together, how a report is read, and the full tech stack. */
export default function AdminSystemPage() {
  const { data: s, error, loading } = useAdminData<AdminSystem>("/admin/system");
  return (
    <>
      <PageHeader title="System" description="What FITSCAN is built with, where each part runs, and its live status. Keys and passwords are never shown here." />
      <LoadState error={error} loading={loading && !s} />
      {s && (
        <div className="space-y-6">
          <p className="flex items-center gap-2 text-sm font-medium text-green-800"><CheckCircle2 className="h-4 w-4" />Server and database are responding · version {s.version} · {s.environment}</p>
          <Architecture s={s} />
          <Pipeline s={s} />
          <Stack s={s} />
          <Settings s={s} />
        </div>
      )}
    </>
  );
}

// ------------------------------------------------------------------ status dot (state = colour + text)
function State({ on, label }: { on: boolean; label: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium ring-1",
      on ? "bg-green-50 text-green-800 ring-green-200" : "bg-slate-50 text-slate-600 ring-slate-200")}>
      <span className={cn("h-1.5 w-1.5 rounded-full", on ? "bg-green-600" : "bg-slate-400")} aria-hidden />{label}
    </span>
  );
}

// ------------------------------------------------------------------ 1. architecture
function Node({ icon: I, title, host, children, tone = "brand", state }: {
  icon: Icon; title: string; host: string; children: React.ReactNode; tone?: "brand" | "ai" | "slate"; state?: React.ReactNode;
}) {
  const ring = { brand: "border-brand-200 bg-white", ai: "border-ai-100 bg-white", slate: "border-slate-200 bg-white" }[tone];
  const chip = { brand: "bg-brand-50 text-brand-700", ai: "bg-ai-50 text-ai-700", slate: "bg-slate-100 text-slate-700" }[tone];
  return (
    <div className={cn("flex h-full flex-col rounded-xl border p-4 shadow-sm", ring)}>
      <div className="flex items-start gap-3">
        <span className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-lg", chip)}><I className="h-5 w-5" aria-hidden /></span>
        <div className="min-w-0">
          <p className="font-semibold text-slate-900">{title}</p>
          <p className="text-xs text-slate-500">{host}</p>
        </div>
      </div>
      <div className="mt-3 flex-1 text-sm text-slate-600">{children}</div>
      {state && <div className="mt-3">{state}</div>}
    </div>
  );
}

function Arrow({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-1 text-slate-400 lg:px-1 lg:py-0" aria-hidden>
      <ArrowRight className="hidden h-5 w-5 lg:block" /><ArrowDown className="h-5 w-5 lg:hidden" />
      {label && <span className="whitespace-nowrap text-[10px] uppercase tracking-wide">{label}</span>}
    </div>
  );
}

function Architecture({ s }: { s: AdminSystem }) {
  return (
    <Card>
      <CardHeader><div><CardTitle className="text-base">How FITSCAN fits together</CardTitle>
        <CardDescription>Every request goes left to right. The website and the API share one address, so login cookies stay first-party.</CardDescription></div></CardHeader>
      <CardContent className="space-y-4">
        <div className="grid items-stretch gap-1 lg:grid-cols-[1fr_auto_1fr_auto_1.2fr_auto_1fr]">
          <Node icon={MonitorSmartphone} title="Client" host="Browser or phone" tone="slate">
            Clients upload reports, check values, read explanations. Admins use this panel.
          </Node>
          <Arrow label="HTTPS" />
          <Node icon={Globe} title="Website" host="Vercel · fitscan-smoky.vercel.app" state={<State on label="Live" />}>
            Next.js 15 + React 19 pages. Forwards <code className="text-xs">/api/v1/*</code> to the API.
          </Node>
          <Arrow label="/api/v1" />
          <Node icon={Server} title="API & report reader" host="Render · Docker · Singapore" state={<State on label={`Live · ${s.environment}`} />}>
            Python FastAPI. Reads reports (OCR), matches tests, works out High/Low from the lab&apos;s range, explains results.
          </Node>
          <Arrow label="SQL" />
          <Node icon={Database} title="Database & files" host={s.database === "postgresql" ? "Neon · PostgreSQL · Singapore" : `Local · ${s.database}`} state={<State on label="Connected" />}>
            Accounts, reports, results, explanations, activity log - and the uploaded files ({s.storage} storage).
          </Node>
        </div>
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Services the API calls</p>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Node icon={Bot} title="Chatbot" host={s.gemini_model ? `Google Gemini · ${s.gemini_model}` : "Google Gemini"} tone="ai"
              state={<State on={s.chatbot !== "offline answers"} label={s.chatbot === "offline answers" ? "Off - offline answers" : `On · ${s.chatbot}`} />}>
              &quot;Talk to assistant&quot; and &quot;what is this term?&quot; answers, grounded in the knowledge library.
            </Node>
            <Node icon={Sparkles} title="Report explanations" host={s.llm_model ? `Anthropic Claude · ${s.llm_model}` : "Anthropic Claude (optional)"} tone="ai"
              state={<State on={s.explanations !== "built-in templates"} label={s.explanations === "built-in templates" ? "Built-in templates (no key)" : `On · ${s.explanations}`} />}>
              Plain-language notes per value. Every AI text passes the safety check and is labelled AI-generated.
            </Node>
            <Node icon={MapPin} title="Centre & doctor search" host={s.centre_search} tone="slate" state={<State on label={`On · ${s.centre_search}`} />}>
              Nearby labs and doctors by speciality (Overpass + Nominatim; Google Places when a key is added).
            </Node>
            <Node icon={Mail} title="Weekly email" host="Resend" tone="slate"
              state={<State on={s.email !== "not connected"} label={s.email === "not connected" ? "Not connected yet" : "On"} />}>
              Monday summary to the owner - totals only, no client data.
            </Node>
          </div>
        </div>
        <div className="flex flex-col gap-3 rounded-xl border border-dashed border-slate-300 p-4 sm:flex-row sm:items-center">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700"><GitBranch className="h-5 w-5" /></span>
          <p className="text-sm text-slate-600"><span className="font-semibold text-slate-900">GitHub</span> holds the code. Every push to <code className="text-xs">main</code> rebuilds the
            website on Vercel; the API is redeployed on Render. GitHub Actions run the tests and ping the API every 10 minutes so the free server doesn&apos;t sleep.</p>
        </div>
      </CardContent>
    </Card>
  );
}

// ------------------------------------------------------------------ 2. report pipeline
function Pipeline({ s }: { s: AdminSystem }) {
  const steps: { icon: Icon; title: string; tech: string; text: string; ai?: boolean }[] = [
    { icon: FileText, title: "Open the file", tech: "PyMuPDF", text: "Uses the PDF's own text when it can be trusted; straightens rotated pages." },
    { icon: ImageIcon, title: "Clean the image", tech: "OpenCV", text: "Scans and photos: deskew, contrast, noise." },
    { icon: ScanText, title: "Read the text", tech: `${s.ocr_engine === "rapidocr" ? "RapidOCR" : s.ocr_engine} · PP-OCR on ONNX`, text: "OCR in page strips, so small print is read on a small server." },
    { icon: TableProperties, title: "Find result rows", tech: "Layout parser", text: "Works on any lab's layout - no per-lab templates. Skips headers, notes, footers." },
    { icon: TestTube2, title: "Recognise tests", tech: `Dictionary · ${s.tests_in_dictionary} tests + RapidFuzz`, text: "Matches printed names, abbreviations and OCR typos." },
    { icon: Ruler, title: "High / Low", tech: "Rules, no AI", text: "Always from the range printed on the lab's own report." },
    { icon: ShieldCheck, title: "Sanity checks", tech: "NHANES + UCI statistics", text: "Flags reading slips (e.g. a lost decimal point) and low confidence." },
    { icon: UserCheck, title: "Client review", tech: "Website", text: "Client confirms or fixes values; only confirmed values are explained." },
    { icon: BrainCircuit, title: "Explain", tech: `Knowledge library (${s.kb_articles}) + ${s.explanations === "built-in templates" ? "templates" : "Claude"}`, text: "Cited, plain-language notes; safety check blocks diagnosis or dosing advice.", ai: true },
  ];
  return (
    <Card>
      <CardHeader><div><CardTitle className="text-base">How a report is read</CardTitle>
        <CardDescription>From upload to explanation, in order. About 2 seconds for a digital PDF, about 90 seconds for a 2-page scan on the current server.</CardDescription></div></CardHeader>
      <CardContent>
        <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {steps.map(({ icon: I, title, tech, text, ai }, i) => (
            <li key={title} className={cn("relative rounded-xl border p-3", ai ? "border-ai-100 bg-ai-50/40" : "border-slate-200 bg-white")}>
              <div className="flex items-center gap-2">
                <span className={cn("flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold", ai ? "bg-ai-600 text-white" : "bg-brand-700 text-white")}>{i + 1}</span>
                <I className={cn("h-4 w-4", ai ? "text-ai-700" : "text-brand-700")} aria-hidden />
                <span className="font-semibold text-slate-900">{title}</span>
              </div>
              <p className="mt-1.5 text-xs font-medium text-slate-500">{tech}</p>
              <p className="mt-1 text-sm text-slate-600">{text}</p>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

// ------------------------------------------------------------------ 3. tech stack
const STACK: { layer: string; icon: Icon; where: string; items: [string, string][] }[] = [
  { layer: "Website", icon: Globe, where: "Vercel", items: [
    ["Next.js 15 (App Router)", "pages & routing"], ["React 19", "user interface"], ["TypeScript (strict)", "safer code"],
    ["Tailwind CSS", "styling"], ["Recharts", "charts"], ["Leaflet + OpenStreetMap", "centre maps"], ["lucide-react", "icons"]] },
  { layer: "API", icon: Server, where: "Render (Docker)", items: [
    ["Python 3.11", "language"], ["FastAPI + Uvicorn", "web API"], ["Pydantic v2", "data validation"],
    ["SQLAlchemy 2 + Alembic", "database access & migrations"], ["JWT in httpOnly cookies", "login sessions"], ["bcrypt", "password hashing"]] },
  { layer: "Report reading", icon: FileSearch, where: "inside the API", items: [
    ["PyMuPDF", "PDF text & rendering"], ["OpenCV", "image clean-up"], ["RapidOCR (PP-OCR, ONNX Runtime)", "printed-text OCR"],
    ["RapidFuzz", "typo-tolerant name matching"], ["Rule engine", "ranges, High/Low, confidence"]] },
  { layer: "AI & knowledge", icon: BrainCircuit, where: "API + external", items: [
    ["Google Gemini", "chatbot"], ["Anthropic Claude (optional)", "report explanations"], ["TF-IDF retriever (NumPy)", "finds cited articles"],
    ["Knowledge library", "MedlinePlus, NIH, NHS summaries"], ["Safety validator", "blocks diagnosis / dosing text"]] },
  { layer: "Data", icon: Database, where: "Neon + repo", items: [
    ["PostgreSQL (Neon)", "all app data and files"], ["Test dictionary", "452 tests, 2,100+ printed names"],
    ["NHANES + UCI statistics", "410k values for sanity checks"], ["Synthetic test reports", "accuracy testing - no real patients"]] },
  { layer: "Hosting & delivery", icon: Cloud, where: "cloud", items: [
    ["Vercel", "website hosting"], ["Render", "API hosting"], ["Neon", "managed Postgres"], ["GitHub + Actions", "code, CI, keep-awake"],
    ["Resend", "weekly email"], ["OpenStreetMap / Google Places", "centre search"]] },
  { layer: "Quality", icon: ListChecks, where: "every change", items: [
    ["pytest", "backend tests"], ["Playwright", "end-to-end browser tests"], ["ruff + black", "code style"], ["Evaluation suite", "reading accuracy report"]] },
];

function Stack({ s }: { s: AdminSystem }) {
  return (
    <Card>
      <CardHeader><div><CardTitle className="text-base">Tech stack</CardTitle>
        <CardDescription>Everything the project uses, grouped by layer, with where it runs.</CardDescription></div></CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {STACK.map(({ layer, icon: I, where, items }) => (
          <section key={layer} className="rounded-xl border border-slate-200 p-4">
            <div className="mb-3 flex items-center justify-between gap-2">
              <p className="flex items-center gap-2 font-semibold text-slate-900"><I className="h-4 w-4 text-brand-700" aria-hidden />{layer}</p>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">{where}</span>
            </div>
            <ul className="space-y-1.5 text-sm">
              {items.map(([name, what]) => (
                <li key={name} className="flex items-baseline justify-between gap-3">
                  <span className="font-medium text-slate-800">{name.replace("452", String(s.tests_in_dictionary))}</span>
                  <span className="text-right text-xs text-slate-500">{what.replace("452", String(s.tests_in_dictionary))}</span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </CardContent>
    </Card>
  );
}

// ------------------------------------------------------------------ 4. current settings
function Settings({ s }: { s: AdminSystem }) {
  const rows: [string, string | number][] = [
    ["Database", s.database], ["File storage", s.storage], ["OCR engine", s.ocr_engine], ["Tests in dictionary", s.tests_in_dictionary],
    ["Knowledge articles", s.kb_articles], ["Max upload", `${s.max_upload_mb} MB`], ["Guest data kept for", `${s.guest_retention_hours} hours`],
    ["Chatbot", s.chatbot], ["Explanations", s.explanations], ["Centre search", s.centre_search], ["Weekly email", s.email],
  ];
  return (
    <Card>
      <CardHeader><div><CardTitle className="flex items-center gap-2 text-base"><Code2 className="h-4 w-4" />Current settings</CardTitle></div></CardHeader>
      <CardContent>
        <dl className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-2 xl:grid-cols-3">
          {rows.map(([k, v]) => <div key={k} className="flex justify-between gap-3 border-b border-slate-100 pb-1.5"><dt className="text-slate-500">{k}</dt><dd className="font-medium text-slate-900">{v}</dd></div>)}
        </dl>
      </CardContent>
    </Card>
  );
}
