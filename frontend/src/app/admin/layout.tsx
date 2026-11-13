"use client";
import { Activity, Database, FileText, LayoutDashboard, Mail, Server, ShieldCheck, Users, UserCog } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { RoleBadge } from "@/components/admin/ui";
import { buttonVariants } from "@/components/ui/button";
import { Empty, Skeleton } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/admin", label: "Overview", Icon: LayoutDashboard, exact: true },
  { href: "/admin/clients", label: "Clients", Icon: Users },
  { href: "/admin/reports", label: "Reports", Icon: FileText },
  { href: "/admin/dataset", label: "Dataset", Icon: Database },
  { href: "/admin/team", label: "Admin team", Icon: UserCog },
  { href: "/admin/activity", label: "Activity log", Icon: Activity },
  { href: "/admin/weekly-email", label: "Weekly email", Icon: Mail },
  { href: "/admin/system", label: "System", Icon: Server },
];

/** Admin shell (FR-ADM): side navigation + access guard. The server enforces access on every request too. */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();

  if (loading) return <Skeleton className="h-64" />;
  if (!user?.is_admin) {
    return (
      <Empty icon={<ShieldCheck className="h-8 w-8" />} title="Admins only">
        {user ? "Your account doesn't have admin access." : "Log in with an admin account to open the admin panel."}
        {!user && <div className="mt-4"><Link href="/login?next=/admin" className={buttonVariants()}>Log in</Link></div>}
      </Empty>
    );
  }

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      <aside className="lg:w-56 lg:shrink-0">
        <div className="mb-3 flex items-center gap-2 px-2">
          <ShieldCheck className="h-5 w-5 text-brand-700" />
          <span className="font-semibold text-slate-900">Admin panel</span>
          {user.admin_role && <RoleBadge role={user.admin_role} />}
        </div>
        <nav aria-label="Admin" className="flex gap-1 overflow-x-auto lg:flex-col">
          {NAV.map(({ href, label, Icon, exact }) => {
            const active = exact ? pathname === href : pathname.startsWith(href);
            return (
              <Link key={href} href={href} aria-current={active ? "page" : undefined}
                className={cn("flex items-center gap-2 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium",
                  active ? "bg-brand-50 text-brand-800" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900")}>
                <Icon className="h-4 w-4" />{label}
              </Link>
            );
          })}
        </nav>
        <p className="mt-4 hidden px-3 text-xs text-slate-500 lg:block">
          Client health data is confidential. Every view and change you make here is recorded in the activity log.
        </p>
      </aside>
      <section className="min-w-0 flex-1">{children}</section>
    </div>
  );
}
