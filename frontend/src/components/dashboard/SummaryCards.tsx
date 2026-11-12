import { ClipboardCheck, FileText, FlaskConical, TriangleAlert } from "lucide-react";
import Link from "next/link";
import type { DashboardData } from "@/lib/types";

export function SummaryCards({ cards }: { cards: DashboardData["cards"] }) {
  const items = [
    { label: "Total Reports", value: cards.total_reports, Icon: FileText, href: "/history", tone: "text-brand-700 bg-brand-50" },
    { label: "Tests Analyzed", value: cards.tests_analyzed, Icon: FlaskConical, href: "/history", tone: "text-sky-700 bg-sky-50" },
    { label: "Outside Lab Range", value: cards.out_of_range, Icon: TriangleAlert, href: "#findings", tone: "text-amber-700 bg-amber-50" },
    { label: "Reports to Review", value: cards.to_review, Icon: ClipboardCheck, href: "/history", tone: "text-violet-700 bg-violet-50" },
  ];
  return (
    <section aria-label="Summary" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {items.map(({ label, value, Icon, href, tone }) => (
        <Link key={label} href={href} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-brand-300">
          <div className={`mb-3 inline-flex rounded-lg p-2 ${tone}`}><Icon className="h-5 w-5" aria-hidden /></div>
          <p className="text-2xl font-bold text-slate-900">{value}</p>
          <p className="text-sm text-slate-500">{label}</p>
        </Link>
      ))}
    </section>
  );
}
