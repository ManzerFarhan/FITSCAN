import { FileUp, GitCompare, History, MapPin } from "lucide-react";
import Link from "next/link";

const ACTIONS = [
  { label: "Upload Lab Report", href: "/analysis", Icon: FileUp },
  { label: "Find Centres", href: "/tests", Icon: MapPin },
  { label: "View History", href: "/history", Icon: History },
  { label: "Compare Reports", href: "/history?compare=1", Icon: GitCompare },
];

export function QuickActions() {
  return (
    <nav aria-label="Quick actions" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {ACTIONS.map(({ label, href, Icon }) => (
        <Link key={label} href={href}
          className="flex flex-col items-center gap-2 rounded-xl border border-slate-200 bg-white p-4 text-center text-sm font-medium text-slate-700 shadow-sm transition hover:border-brand-300 hover:text-brand-800">
          <Icon className="h-6 w-6 text-brand-700" aria-hidden />{label}
        </Link>
      ))}
    </nav>
  );
}
