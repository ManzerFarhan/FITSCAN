"use client";
import { ChevronDown, FlaskConical, History, LayoutDashboard, Lock, LogIn, LogOut, Menu, ScanLine, Upload, User, X } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard", Icon: LayoutDashboard },
  { href: "/analysis", label: "Upload & Analysis", Icon: ScanLine },
  { href: "/tests", label: "Tests & Centres", Icon: FlaskConical, members: true },  // log in to unlock
  { href: "/history", label: "History", Icon: History },
  { href: "/profile", label: "Profile", Icon: User },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [mobile, setMobile] = useState(false);
  const [menu, setMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setMobile(false); setMenu(false); }, [pathname]);
  useEffect(() => {
    const close = (e: MouseEvent) => menuRef.current && !menuRef.current.contains(e.target as Node) && setMenu(false);
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, []);

  const first = user?.full_name?.split(" ")[0];

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-4">
        <button className="rounded-lg p-2 hover:bg-slate-100 lg:hidden" onClick={() => setMobile((m) => !m)}
          aria-label={mobile ? "Close menu" : "Open menu"} aria-expanded={mobile}>
          {mobile ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
        <Link href="/dashboard" className="flex items-center gap-2 font-bold text-slate-900">
          <Image src="/logo.svg" alt="" width={32} height={32} priority />
          <span className="text-lg tracking-tight">FITSCAN</span>
        </Link>
        <nav className="ml-4 hidden items-center gap-1 lg:flex" aria-label="Main">
          {NAV.map(({ href, label, members }) => (
            <Link key={href} href={href} aria-current={pathname.startsWith(href) ? "page" : undefined}
              className={cn("inline-flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium",
                pathname.startsWith(href) ? "bg-brand-50 text-brand-800" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900")}>
              {label}{members && !user && <Lock className="h-3 w-3 text-slate-400" aria-label="Log in to unlock" />}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-1 sm:gap-2">
          <span className="hidden text-sm text-slate-600 xl:inline">{first ? `Welcome, ${first}` : "Welcome, guest"}</span>
          <Link href="/analysis" className={cn(buttonVariants({ size: "sm" }), "hidden sm:inline-flex")}>
            <Upload className="h-4 w-4" />Upload
          </Link>
          <div className="relative" ref={menuRef}>
            <button onClick={() => setMenu((m) => !m)} aria-expanded={menu} aria-label="Profile menu"
              className="flex items-center gap-1 rounded-lg p-1.5 hover:bg-slate-100">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-800">
                {(first?.[0] ?? "G").toUpperCase()}
              </span>
              <ChevronDown className="h-4 w-4 text-slate-500" />
            </button>
            {menu && (
              <div className="absolute right-0 z-40 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-1 shadow-lg">
                <p className="truncate px-3 py-2 text-xs text-slate-500">{user ? user.email : "Guest - data kept for 24 hours"}</p>
                <Link href="/profile" className="block rounded-lg px-3 py-2 text-sm hover:bg-slate-50">Profile & settings</Link>
                {user ? (
                  <button onClick={async () => { await logout(); router.push("/dashboard"); router.refresh(); }}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-slate-50">
                    <LogOut className="h-4 w-4" />Log out
                  </button>
                ) : (
                  <>
                    <Link href="/login" className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-slate-50"><LogIn className="h-4 w-4" />Log in</Link>
                    <Link href="/register" className="block rounded-lg px-3 py-2 text-sm font-medium text-brand-700 hover:bg-slate-50">Create free account</Link>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      {mobile && (
        <nav className="border-t border-slate-200 bg-white px-4 py-2 lg:hidden" aria-label="Main mobile">
          {NAV.map(({ href, label, Icon, members }) => (
            <Link key={href} href={href} className={cn("flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium",
              pathname.startsWith(href) ? "bg-brand-50 text-brand-800" : "text-slate-700")}>
              <Icon className="h-4 w-4" />{label}{members && !user && <Lock className="h-3 w-3 text-slate-400" aria-label="Log in to unlock" />}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
