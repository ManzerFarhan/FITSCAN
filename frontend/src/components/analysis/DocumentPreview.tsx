"use client";
/* eslint-disable @next/next/no-img-element */
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { fileUrl, pageImageUrl } from "@/lib/api";
import type { BBox } from "@/lib/types";
import { cn } from "@/lib/utils";

export interface Highlight { id: string; bbox: BBox; tone: "uncertain" | "active" | "normal" }

/** Server-rendered page image with normalized bbox overlays (FR-LAB-9, FR-RX-6). */
export function PageWithHighlights({ docId, page, highlights = [], activeId, onSelect, className }: {
  docId: string; page: number; highlights?: Highlight[]; activeId?: string | null; onSelect?: (id: string) => void; className?: string;
}) {
  return (
    <div className={cn("relative w-full overflow-hidden rounded-lg border border-slate-200 bg-white", className)}>
      <img src={pageImageUrl(docId, page)} alt={`Page ${page} of your document`} className="block w-full" />
      {highlights.filter((h) => h.bbox.page === page).map((h) => (
        <button key={h.id} type="button" onClick={() => onSelect?.(h.id)} aria-label="Show this field"
          className={cn("absolute rounded-sm border-2 transition",
            h.id === activeId ? "border-brand-600 bg-brand-400/20 ring-2 ring-brand-300" :
              h.tone === "uncertain" ? "border-amber-500 bg-amber-300/25" : "border-transparent hover:border-sky-400")}
          style={{
            left: `${h.bbox.x0 * 100 - 0.5}%`, top: `${h.bbox.y0 * 100 - 0.3}%`,
            width: `${(h.bbox.x1 - h.bbox.x0) * 100 + 1}%`, height: `${(h.bbox.y1 - h.bbox.y0) * 100 + 0.6}%`,
          }} />
      ))}
    </div>
  );
}

/** Zoomed crop around one field, for side-by-side checking. */
export function FieldCrop({ docId, bbox, pageAspect = 1.414 }: { docId: string; bbox: BBox; pageAspect?: number }) {
  // Show the full row width (labs print name, value and range on one line) plus a little vertical context.
  const x0 = 0.03, x1 = 0.97;
  const y0 = Math.max(0, bbox.y0 - 0.012), y1 = Math.min(1, bbox.y1 + 0.012);
  const w = x1 - x0, h = y1 - y0;
  const pos = (start: number, size: number) => (size >= 1 ? 0 : (start / (1 - size)) * 100);
  return (
    <div role="img" aria-label="Crop of the original document around this value"
      className="w-full rounded-md border border-slate-200 bg-white bg-no-repeat"
      style={{
        aspectRatio: `${w / (h * pageAspect)}`,
        backgroundImage: `url(${pageImageUrl(docId, bbox.page)})`,
        backgroundSize: `${100 / w}% auto`,
        backgroundPosition: `${pos(x0, w)}% ${pos(y0, h)}%`,
      }} />
  );
}

/** FR-UPL-2 preview: local file before upload, server pages after. */
export function DocumentPreview({ file, docId, pages = 1, highlights, activeId, onSelect }: {
  file?: File | null; docId?: string | null; pages?: number; highlights?: Highlight[]; activeId?: string | null; onSelect?: (id: string) => void;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!file || docId) return;
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file, docId]);

  useEffect(() => {
    const active = highlights?.find((h) => h.id === activeId);
    if (active) setPage(active.bbox.page);
  }, [activeId, highlights]);

  if (docId) {
    return (
      <div className="space-y-2">
        <PageWithHighlights docId={docId} page={page} highlights={highlights} activeId={activeId} onSelect={onSelect} />
        <div className="flex items-center justify-between gap-2 text-sm">
          <div className="flex items-center gap-1">
            <Button variant="secondary" size="icon" aria-label="Previous page" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}><ChevronLeft className="h-4 w-4" /></Button>
            <span className="px-2 text-slate-600">Page {page} of {pages}</span>
            <Button variant="secondary" size="icon" aria-label="Next page" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}><ChevronRight className="h-4 w-4" /></Button>
          </div>
          <a href={fileUrl(docId)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-700 hover:underline">
            Open original <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>
    );
  }
  if (!file || !url) return null;
  return file.type === "application/pdf"
    ? <object data={url} type="application/pdf" className="h-[480px] w-full rounded-lg border border-slate-200" aria-label="PDF preview">
        <p className="p-4 text-sm text-slate-500">PDF preview isn't available in this browser - the file will still upload.</p>
      </object>
    : <img src={url} alt="Preview of the selected file" className="max-h-[480px] w-full rounded-lg border border-slate-200 object-contain" />;
}
