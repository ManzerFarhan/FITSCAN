"use client";
import { CheckCircle2, FileUp, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { buttonVariants } from "@/components/ui/button";
import { CenterModal } from "./LoginToUnlock";

const SEEN_KEY = "fitscan.welcomeSeen";
const SKIP = ["/login", "/register", "/reset-password", "/privacy", "/terms", "/analysis"];

/** First visit (desktop or phone): a centred pop-up inviting people to upload their blood report. */
export function WelcomeModal() {
  const pathname = usePathname() || "/";
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (SKIP.some((p) => pathname.startsWith(p))) return;
    try { if (!localStorage.getItem(SEEN_KEY)) setOpen(true); } catch { /* storage unavailable */ }
  }, [pathname]);

  const close = () => {
    setOpen(false);
    try { localStorage.setItem(SEEN_KEY, "1"); } catch { /* ignore */ }
  };

  return (
    <CenterModal open={open} onClose={close} label="Welcome to FITSCAN">
      <div className="space-y-5 text-center">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-700 text-white"><FileUp className="h-7 w-7" aria-hidden /></span>
        <div>
          <h2 className="text-xl font-bold text-slate-900">Upload your blood test report</h2>
          <p className="mt-1 text-sm text-slate-600">FITSCAN reads your lab report and explains every value in plain language - in about a minute.</p>
        </div>
        <ol className="space-y-2 text-left text-sm text-slate-700">
          {[
            [FileUp, "Upload a PDF or a clear photo of your printed lab report"],
            [CheckCircle2, "Check the values we read (or let FITSCAN auto-check them)"],
            [Sparkles, "Get a simple AI explanation you can discuss with your doctor"],
          ].map(([Icon, text], i) => {
            const I = Icon as typeof FileUp;
            return (
              <li key={i} className="flex items-start gap-3 rounded-lg bg-slate-50 p-2.5">
                <I className="mt-0.5 h-4 w-4 shrink-0 text-brand-700" aria-hidden />{text as string}
              </li>
            );
          })}
        </ol>
        <div className="space-y-2">
          <Link href="/analysis" onClick={close} className={buttonVariants({ size: "lg", className: "w-full" })}>
            <FileUp className="h-5 w-5" />Upload my blood report
          </Link>
          <button onClick={close} className="text-sm text-slate-500 hover:underline">I&apos;ll look around first</button>
        </div>
        <p className="flex items-center justify-center gap-1.5 text-xs text-slate-500">
          <ShieldCheck className="h-3.5 w-3.5" aria-hidden />Free to try. No sign-up needed. Not a diagnosis.
        </p>
      </div>
    </CenterModal>
  );
}
