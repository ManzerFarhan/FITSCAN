"use client";
import { Bot, Download, ExternalLink, FileText, Trash2 } from "lucide-react";
import Link from "next/link";
import { DocStatusBadge } from "@/components/ui/badges";
import { Button } from "@/components/ui/button";
import { Empty } from "@/components/ui/misc";
import { fileUrl, summaryPdfUrl } from "@/lib/api";
import { CATEGORY_LABELS } from "@/lib/constants";
import type { DocumentOut } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

/** FR-HIST-1/2: list + per-document actions; lab reports can be selected for comparison. */
export function DocumentList({ docs, selected, onToggle, onDelete, compareMode }: {
  docs: DocumentOut[]; selected: string[]; onToggle: (id: string) => void; onDelete: (d: DocumentOut) => void; compareMode: boolean;
}) {
  if (docs.length === 0) {
    return <Empty icon={<FileText className="h-8 w-8" />} title="No documents match"><Link href="/analysis" className="text-brand-700 underline">Upload a document</Link></Empty>;
  }
  return (
    <ul className="space-y-2">
      {docs.map((d) => {
        const comparable = d.status === "VERIFIED" || d.status === "ANALYZED";
        return (
          <li key={d.id} className={cn("rounded-lg border bg-white p-3", selected.includes(d.id) ? "border-brand-500 ring-2 ring-brand-100" : "border-slate-200")}>
            <div className="flex flex-wrap items-start gap-3">
              {compareMode && (
                <input type="checkbox" className="mt-1 h-4 w-4 accent-brand-700" disabled={!comparable} checked={selected.includes(d.id)}
                  onChange={() => onToggle(d.id)} aria-label={`Select ${d.original_filename} for comparison`}
                  title={comparable ? "" : "Only verified lab reports can be compared"} />
              )}
              <span className="rounded-lg bg-brand-50 p-2 text-brand-700">
                <FileText className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Link href={`/analysis?doc=${d.id}`} className="truncate font-medium text-slate-900 hover:underline">{d.original_filename}</Link>
                  <DocStatusBadge status={d.status} />
                  {d.has_analysis && <span className="inline-flex items-center gap-1 text-xs text-ai-700"><Bot className="h-3 w-3" />AI analysis</span>}
                </div>
                <p className="text-sm text-slate-600">
                  {d.lab_name ?? "Lab not detected"}
                  {d.report_category && ` · ${CATEGORY_LABELS[d.report_category] ?? d.report_category}`}
                </p>
                <p className="text-xs text-slate-500">
                  Report date {formatDate(d.report_date)} · uploaded {formatDate(d.uploaded_at)}
                  {` · ${d.parameter_count} values${d.out_of_range_count ? `, ${d.out_of_range_count} outside range` : ""}`}
                </p>
              </div>
              <div className="flex flex-wrap gap-1">
                <Link href={`/analysis?doc=${d.id}`} className="inline-flex h-8 items-center rounded-lg px-2 text-sm text-slate-700 hover:bg-slate-100">
                  {d.has_analysis ? "Open analysis" : "View data"}
                </Link>
                <a href={fileUrl(d.id)} target="_blank" rel="noreferrer" aria-label="View original" className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100"><ExternalLink className="h-4 w-4" /></a>
                <a href={fileUrl(d.id, true)} aria-label="Download original" className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100"><Download className="h-4 w-4" /></a>
                {d.has_analysis && <a href={summaryPdfUrl(d.id)} className="inline-flex h-8 items-center rounded-lg px-2 text-sm text-ai-700 hover:bg-ai-50">PDF</a>}
                <Button variant="ghost" size="icon" aria-label={`Delete ${d.original_filename}`} onClick={() => onDelete(d)}><Trash2 className="h-4 w-4 text-red-600" /></Button>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
