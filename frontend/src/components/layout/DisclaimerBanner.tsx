import { ShieldAlert } from "lucide-react";
import { DISCLAIMER_TEXT } from "@/lib/constants";
import { cn } from "@/lib/utils";

/** BR-13: the medical disclaimer appears on every page. */
export function DisclaimerBanner({ compact, className }: { compact?: boolean; className?: string }) {
  return (
    <div className={cn("flex items-start gap-2 rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 text-orange-900",
      compact ? "text-xs" : "text-sm", className)} role="note" aria-label="Medical disclaimer">
      <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <p>{DISCLAIMER_TEXT}</p>
    </div>
  );
}
