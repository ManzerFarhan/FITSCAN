import { CheckCircle2, FileUp, MessageSquareText, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const STEPS = [
  { Icon: FileUp, title: "Upload your report", text: "A PDF or a clear photo of your printed blood test report." },
  { Icon: CheckCircle2, title: "Check what we read", text: "Every value next to your lab's own normal range - fix anything we got wrong." },
  { Icon: Sparkles, title: "Get it explained", text: "Plain-language notes and questions you can take to your doctor." },
];

/** Dashboard for someone with no reports yet: one clear next step instead of many empty cards. */
export function FirstReportPanel({ isGuest }: { isGuest: boolean }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-brand-200 bg-gradient-to-b from-brand-50 to-white" aria-labelledby="first-report">
      <div className="px-5 py-8 text-center sm:px-10 sm:py-12">
        <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-700 text-white shadow-sm">
          <FileUp className="h-8 w-8" aria-hidden />
        </span>
        <h2 id="first-report" className="mt-5 text-2xl font-bold text-slate-900 sm:text-3xl">Upload your first report</h2>
        <p className="mx-auto mt-2 max-w-xl text-slate-600">
          FITSCAN reads your lab report and explains each value in plain language - in about a minute.
          Your charts, trends and findings will appear here afterwards.
        </p>
        <Link href="/analysis" className={cn(buttonVariants({ size: "lg" }), "mt-6 w-full sm:w-auto")}>
          <FileUp className="h-5 w-5" />Upload my blood report
        </Link>
        <p className="mt-3 flex items-center justify-center gap-1.5 text-xs text-slate-500">
          <ShieldCheck className="h-3.5 w-3.5" aria-hidden />
          {isGuest ? "Free, no sign-up needed. As a guest your report is kept for 24 hours." : "Private to your account. Not a diagnosis."}
        </p>
      </div>
      <ol className="grid gap-px border-t border-brand-100 bg-brand-100 sm:grid-cols-3">
        {STEPS.map(({ Icon, title, text }, i) => (
          <li key={title} className="flex gap-3 bg-white p-5">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-50 text-sm font-semibold text-brand-800">{i + 1}</span>
            <div>
              <p className="flex items-center gap-1.5 font-medium text-slate-900"><Icon className="h-4 w-4 text-brand-700" aria-hidden />{title}</p>
              <p className="mt-0.5 text-sm text-slate-600">{text}</p>
            </div>
          </li>
        ))}
      </ol>
      <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 border-t border-brand-100 bg-white px-5 py-3 text-sm">
        <span className="flex items-center gap-1.5 text-slate-600"><MessageSquareText className="h-4 w-4" aria-hidden />Questions? Use &quot;Talk to assistant&quot; at the bottom right.</span>
        {isGuest && <Link href="/register" className="font-medium text-brand-700 hover:underline">Create a free account to keep your history</Link>}
      </div>
    </section>
  );
}
