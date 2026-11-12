import Link from "next/link";
import { isPlaceholder } from "@/lib/site";
import { cn } from "@/lib/utils";

export type LegalSection = { id: string; title: string; body: React.ReactNode };

/** Placeholder-aware value: anything still in [brackets] is highlighted so it can't be missed before launch. */
export function V({ children }: { children: string }) {
  return isPlaceholder(children)
    ? <mark className="rounded bg-amber-100 px-1 text-amber-900" title="Placeholder - replace before launch">{children}</mark>
    : <>{children}</>;
}

/** Shared layout for the Privacy Policy and Terms & Conditions: summary box, table of contents, numbered sections. */
export function LegalDocument({ title, effective, intro, summary, sections, other }: {
  title: string; effective: string; intro: React.ReactNode; summary: string[]; sections: LegalSection[];
  other: { href: string; label: string };
}) {
  return (
    <article className="mx-auto max-w-4xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-slate-900">{title}</h1>
        <p className="text-sm text-slate-500">Effective date: {effective}</p>
        <div className="text-slate-700">{intro}</div>
      </header>

      <section aria-labelledby="summary" className="rounded-xl border border-brand-100 bg-brand-50/60 p-5">
        <h2 id="summary" className="mb-2 font-semibold text-slate-900">The short version</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">{summary.map((s) => <li key={s}>{s}</li>)}</ul>
        <p className="mt-3 text-xs text-slate-500">This summary is for convenience. The full text below is what applies.</p>
      </section>

      <div className="grid gap-6 lg:grid-cols-4">
        <nav aria-label="Contents" className="lg:col-span-1">
          <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm lg:sticky lg:top-20">
            <p className="mb-2 font-semibold text-slate-900">Contents</p>
            <ol className="space-y-1.5">
              {sections.map((s, i) => (
                <li key={s.id}><a href={`#${s.id}`} className="text-slate-600 hover:text-brand-700 hover:underline">{i + 1}. {s.title}</a></li>
              ))}
            </ol>
          </div>
        </nav>
        <div className="space-y-4 lg:col-span-3">
          {sections.map((s, i) => (
            <section key={s.id} id={s.id} className="scroll-mt-24 rounded-xl border border-slate-200 bg-white p-5">
              <h2 className="mb-3 text-lg font-semibold text-slate-900">{i + 1}. {s.title}</h2>
              <div className={cn("space-y-3 text-sm leading-6 text-slate-700",
                "[&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pl-5 [&_strong]:text-slate-900 [&_a]:text-brand-700 [&_a]:underline")}>
                {s.body}
              </div>
            </section>
          ))}
          <p className="text-sm text-slate-500">See also our <Link href={other.href} className="text-brand-700 underline">{other.label}</Link>.</p>
        </div>
      </div>
    </article>
  );
}
