import { Download } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { summaryPdfUrl } from "@/lib/api";

export function DownloadSummaryButton({ docId }: { docId: string }) {
  return (
    <a href={summaryPdfUrl(docId)} className={buttonVariants({ variant: "secondary" })} download>
      <Download className="h-4 w-4" />Download PDF summary
    </a>
  );
}
