"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/form";
import { Alert, Progress } from "@/components/ui/misc";
import { ApiError, uploadWithProgress } from "@/lib/api";
import { ACCEPTED_EXT, CATEGORY_LABELS, REPORT_CATEGORIES } from "@/lib/constants";
import { validateFile } from "@/lib/utils";

/** FR-PROF-2 / API-18 / BR-14: older documents with their ACTUAL report date. Same pipeline as normal uploads. */
export function HistoricalUpload() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [date, setDate] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return setError("Choose a file.");
    const v = validateFile(file);
    if (v) return setError(v);
    setError(null); setProgress(0);
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", "LAB_REPORT");
    if (date) form.append("report_date", date);
    if (category) form.append("category", category);
    if (description) form.append("description", description);
    try {
      const res = await uploadWithProgress<{ document_id: string }>("/profile/historical-documents", form, setProgress);
      router.push(`/analysis?doc=${res.document_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
      setProgress(null);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <p className="text-sm text-slate-600">
        Add older lab reports to build your history. Enter the date printed on the report if you know it - we never use the upload date as the report date.
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="File" htmlFor="h-file"><Input id="h-file" type="file" accept={ACCEPTED_EXT.join(",")} className="py-1.5" onChange={(e) => setFile(e.target.files?.[0] ?? null)} /></Field>
        <Field label="Actual report date" htmlFor="h-date" hint="Required later if it can't be read from the document.">
          <Input id="h-date" type="date" value={date} max={new Date().toISOString().slice(0, 10)} onChange={(e) => setDate(e.target.value)} />
        </Field>
        <Field label="Category" htmlFor="h-cat">
          <Select id="h-cat" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">Detect automatically</option>
            {REPORT_CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_LABELS[c]}</option>)}
          </Select>
        </Field>
      </div>
      <Field label="Description (optional)" htmlFor="h-desc"><Textarea id="h-desc" value={description} maxLength={2000} onChange={(e) => setDescription(e.target.value)} /></Field>
      {progress !== null && <Progress value={progress} label="Upload progress" />}
      {error && <Alert tone="error">{error}</Alert>}
      <Button type="submit" disabled={progress !== null}>Upload older lab report</Button>
    </form>
  );
}
