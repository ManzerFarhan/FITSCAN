import { ArrowRight, FileText } from "lucide-react";
import Link from "next/link";
import { DocStatusBadge } from "@/components/ui/badges";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Empty } from "@/components/ui/misc";
import { CATEGORY_LABELS } from "@/lib/constants";
import type { DashboardData } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function LatestReportCard({ report }: { report: DashboardData["latest_report"] }) {
  return (
    <Card>
      <CardHeader><CardTitle>Latest Report</CardTitle></CardHeader>
      <CardContent>
        {!report ? (
          <Empty icon={<FileText className="h-8 w-8" />} title="No lab reports yet">
            <Link href="/analysis" className="text-brand-700 underline">Upload your first report</Link> to see it here.
          </Empty>
        ) : (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <p className="min-w-0 truncate font-medium text-slate-900">{report.original_filename}</p>
              <DocStatusBadge status={report.status} />
            </div>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-3">
              {[
                ["Lab", report.lab_name ?? "-"],
                ["Category", report.report_category ? CATEGORY_LABELS[report.report_category] ?? report.report_category : "-"],
                ["Report date", formatDate(report.report_date)],
                ["Uploaded", formatDate(report.uploaded_at)],
                ["Parameters", String(report.parameter_count)],
              ].map(([k, v]) => (
                <div key={k}><dt className="text-slate-500">{k}</dt><dd className="font-medium text-slate-800">{v}</dd></div>
              ))}
            </dl>
            <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">{report.summary}</p>
            <Link href={`/analysis?doc=${report.id}`} className={buttonVariants({ variant: "secondary", size: "sm" })}>
              View full analysis <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
