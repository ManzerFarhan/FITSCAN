"use client";
import { Activity, Lock, MapPin, MessageCircle, Scale, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** Features that need a free account. Everything else stays open to guests. */
export const MEMBER_FEATURES = [
  { Icon: MapPin, title: "Tests & Centres", text: "Find diagnostic centres near you on a map" },
  { Icon: Activity, title: "Lab health score", text: "Your latest report summarised out of 10" },
  { Icon: Scale, title: "BMI on your dashboard", text: "Add your height and weight (optional)" },
  { Icon: MessageCircle, title: "FITSCAN assistant", text: "Ask questions about your tests and report" },
];

export function authLinks(next: string) {
  const q = `?next=${encodeURIComponent(next)}`;
  return { login: `/login${q}`, register: `/register${q}` };
}

function AuthButtons({ next, onClick, className }: { next: string; onClick?: () => void; className?: string }) {
  // Come back to exactly this page after logging in, including ?doc=... (read after mount; no Suspense needed).
  const [here, setHere] = useState(next);
  useEffect(() => { setHere(window.location.pathname + window.location.search); }, [next]);
  const l = authLinks(here);
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      <Link href={l.register} onClick={onClick} className={buttonVariants()}>Create free account</Link>
      <Link href={l.login} onClick={onClick} className={buttonVariants({ variant: "secondary" })}>Log in</Link>
    </div>
  );
}

/** Shown in place of a members-only feature. `compact` fits inside a dashboard card. */
export function LoginToUnlock({ feature, description, compact }: { feature: string; description: string; compact?: boolean }) {
  const pathname = usePathname() || "/dashboard";
  return (
    <div className={cn("flex flex-col items-center gap-3 rounded-xl border border-dashed border-brand-300 bg-brand-50/50 text-center",
      compact ? "p-5" : "px-6 py-10")}>
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-100 text-brand-800"><Lock className="h-5 w-5" aria-hidden /></span>
      <div>
        <p className="font-semibold text-slate-900">Log in to unlock {feature}</p>
        <p className="mt-1 max-w-md text-sm text-slate-600">{description}</p>
      </div>
      <AuthButtons next={pathname} className="justify-center" />
      {!compact && <p className="text-xs text-slate-500">It&apos;s free. Reports you uploaded as a guest move into your account.</p>}
    </div>
  );
}

/** Centred pop-up that covers the whole screen (desktop and phone). */
export function CenterModal({ open, onClose, label, children }: { open: boolean; onClose: () => void; label: string; children: React.ReactNode }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = ""; };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-label={label} onClick={(e) => e.stopPropagation()}
        className="relative max-h-[92vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
        <button onClick={onClose} aria-label="Close" className="absolute right-3 top-3 rounded p-1 text-slate-500 hover:bg-slate-100"><X className="h-5 w-5" /></button>
        {children}
      </div>
    </div>
  );
}

/** After a guest's analysis: remind them what an account unlocks. */
export function UnlockReminder({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname() || "/analysis";
  return (
    <CenterModal open={open} onClose={onClose} label="Unlock more features">
      <div className="space-y-4 text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-100 text-brand-800"><Lock className="h-6 w-6" aria-hidden /></span>
        <div>
          <h2 className="text-lg font-bold text-slate-900">Your analysis is ready!</h2>
          <p className="mt-1 text-sm text-slate-600">Log in or create a free account to unlock more and keep this report beyond 24 hours.</p>
        </div>
        <ul className="space-y-2 text-left text-sm">
          {MEMBER_FEATURES.map(({ Icon, title, text }) => (
            <li key={title} className="flex items-start gap-3 rounded-lg bg-slate-50 p-2.5">
              <Icon className="mt-0.5 h-4 w-4 shrink-0 text-brand-700" aria-hidden />
              <span><span className="font-medium text-slate-900">{title}</span> <span className="text-slate-600">- {text}</span></span>
            </li>
          ))}
        </ul>
        <AuthButtons next={pathname} onClick={onClose} className="justify-center" />
        <button onClick={onClose} className="text-sm text-slate-500 hover:underline">Maybe later</button>
      </div>
    </CenterModal>
  );
}
