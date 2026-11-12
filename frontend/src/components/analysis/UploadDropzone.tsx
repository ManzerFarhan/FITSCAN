"use client";
import { FileText, FileUp, FlaskConical, X } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Alert, Progress } from "@/components/ui/misc";
import { ACCEPTED_EXT, MAX_UPLOAD_MB } from "@/lib/constants";
import { cn, formatBytes, validateFile } from "@/lib/utils";

/** The "Lab report" card is itself the file picker: click it, or drop a file on it. */
export function UploadDropzone({ file, onFile, onUpload, uploading, progress, disabled }: {
  file: File | null; onFile: (f: File | null) => void; onUpload: () => void;
  uploading: boolean; progress: number; disabled?: boolean;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const locked = disabled || uploading;

  const pick = (f: File | undefined) => {
    if (!f) return;
    const err = validateFile(f);
    setError(err);
    onFile(err ? null : f);
  };

  return (
    <div className="space-y-3">
      <button
        type="button"
        disabled={locked}
        onClick={() => input.current?.click()}
        onDragOver={(e) => { e.preventDefault(); if (!locked) setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); if (!locked) pick(e.dataTransfer.files[0]); }}
        aria-describedby="upload-hint"
        className={cn(
          "group relative flex w-full flex-col items-center gap-4 rounded-2xl border-2 border-dashed bg-white px-5 py-8 text-center transition",
          "sm:flex-row sm:gap-6 sm:px-8 sm:py-10 sm:text-left lg:py-12",
          "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-brand-200 disabled:cursor-not-allowed disabled:opacity-60",
          drag ? "border-brand-500 bg-brand-50" : file ? "border-brand-600 bg-brand-50/40" : "border-brand-300 hover:border-brand-500 hover:bg-brand-50/50",
        )}>
        <span className={cn("flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl transition sm:h-20 sm:w-20",
          drag || file ? "bg-brand-600 text-white" : "bg-brand-50 text-brand-700 group-hover:bg-brand-100")}>
          <FlaskConical className="h-8 w-8 sm:h-10 sm:w-10" aria-hidden />
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-1">
          <span className="text-lg font-semibold text-slate-900 sm:text-xl">Lab report</span>
          <span className="text-sm text-slate-600 sm:text-base">Blood test results with values and reference ranges</span>
          <span id="upload-hint" className="mt-2 text-xs text-slate-500">
            PDF, JPG or PNG · up to {MAX_UPLOAD_MB} MB · PDFs up to 30 pages · printed reports only
          </span>
        </span>
        <span className={cn("inline-flex shrink-0 items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition",
          "w-full justify-center sm:w-auto", file ? "bg-white text-brand-800 ring-1 ring-brand-300" : "bg-brand-700 text-white group-hover:bg-brand-800")}>
          <FileUp className="h-4 w-4" aria-hidden />
          {drag ? "Drop to attach" : file ? "Choose a different file" : "Choose file or drag it here"}
        </span>
      </button>
      <input ref={input} type="file" className="sr-only" accept={ACCEPTED_EXT.join(",")} aria-label="Choose file" tabIndex={-1}
        onChange={(e) => { pick(e.target.files?.[0]); e.target.value = ""; }} />

      {error && <Alert tone="error">{error}</Alert>}
      {file && (
        <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-3 sm:flex-row sm:items-center">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <FileText className="h-8 w-8 shrink-0 text-brand-700" aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-900">{file.name}</p>
              <p className="text-xs text-slate-500">{formatBytes(file.size)}</p>
              {uploading && <Progress value={progress} className="mt-2" label="Upload progress" />}
            </div>
            {!uploading && (
              <button onClick={() => onFile(null)} aria-label="Remove file" className="rounded p-1 text-slate-500 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            )}
          </div>
          <Button onClick={onUpload} disabled={uploading || disabled} className="w-full sm:w-auto">
            {uploading ? `Uploading ${progress}%` : "Upload & process"}
          </Button>
        </div>
      )}
    </div>
  );
}
