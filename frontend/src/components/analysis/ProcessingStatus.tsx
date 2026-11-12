import { Check, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, Spinner } from "@/components/ui/misc";
import { STATUS_STEPS, type DocumentStatus } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function ProcessingStatus({ status, message, onRetry }: { status: DocumentStatus; message?: string | null; onRetry?: () => void }) {
  if (status === "FAILED") {
    return (
      <Alert tone="error" title="We couldn't process this document">
        <p>{message ?? "Please try again."}</p>
        {onRetry && <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}><RotateCcw className="h-4 w-4" />Retry</Button>}
      </Alert>
    );
  }
  const effective = status === "EXTRACTED" ? "NEEDS_VERIFICATION" : status;
  const idx = STATUS_STEPS.findIndex((s) => s.key === effective);
  const working = ["UPLOADED", "PREPROCESSING", "OCR_RUNNING", "EXTRACTING"].includes(status);
  return (
    <div aria-live="polite">
      <ol className="flex items-center gap-1 overflow-x-auto pb-1">
        {STATUS_STEPS.map((s, i) => {
          const done = i < idx || (i === idx && !working && status !== "NEEDS_VERIFICATION" && status !== "EXTRACTED");
          const current = i === idx;
          return (
            <li key={s.key} className="flex shrink-0 items-center gap-1">
              <span className={cn("flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold",
                done ? "bg-brand-600 text-white" : current ? "bg-brand-100 text-brand-800 ring-2 ring-brand-500" : "bg-slate-200 text-slate-500")}>
                {done ? <Check className="h-3.5 w-3.5" /> : current && working ? <Spinner className="h-3.5 w-3.5" /> : i + 1}
              </span>
              <span className={cn("text-xs", current ? "font-semibold text-slate-900" : "text-slate-500")}>{s.label}</span>
              {i < STATUS_STEPS.length - 1 && <span className="mx-1 h-px w-4 bg-slate-300 sm:w-6" />}
            </li>
          );
        })}
      </ol>
      {working && <p className="mt-2 text-sm text-slate-600">Reading your document - scanned pages can take up to a minute.</p>}
      {message && !working && <Alert tone="warning" className="mt-2">{message}</Alert>}
    </div>
  );
}
