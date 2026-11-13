"use client";
import { ArrowRight, MapPin, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { AnalysisPanel, AnalysisTeaser } from "@/components/analysis/AnalysisPanel";
import { DocumentPreview } from "@/components/analysis/DocumentPreview";
import { ProcessingStatus } from "@/components/analysis/ProcessingStatus";
import { UploadDropzone } from "@/components/analysis/UploadDropzone";
import { VerificationTable } from "@/components/analysis/VerificationTable";
import { DocStatusBadge } from "@/components/ui/badges";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, Skeleton } from "@/components/ui/misc";
import { useDocument } from "@/hooks/useDocument";
import { api, ApiError, uploadWithProgress } from "@/lib/api";

function AnalysisInner() {
  const params = useSearchParams();
  const router = useRouter();
  const docParam = params.get("doc");
  const focusParam = params.get("param");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { doc, extraction, setExtraction, error, restart } = useDocument(docParam);

  const upload = async () => {
    if (!file) return;
    setUploading(true); setUploadError(null); setProgress(0);
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", "LAB_REPORT");
    try {
      const res = await uploadWithProgress<{ document_id: string }>("/documents", form, setProgress);
      router.replace(`/analysis?doc=${res.document_id}`);
    } catch (e) {
      setUploadError(e instanceof ApiError ? e.message : "Upload failed.");
    } finally { setUploading(false); }
  };

  const retry = async () => {
    if (!docParam) return;
    try { await api(`/documents/${docParam}/reprocess`, { method: "POST" }); restart(); } catch { /* shown by poll */ }
  };

  const startOver = () => { setFile(null); setExtraction(null); router.replace("/analysis"); };
  const currentStatus = extraction?.document.status ?? doc?.status;
  const verified = currentStatus === "VERIFIED" || currentStatus === "ANALYZED";
  const centresHref = docParam ? `/tests?doc=${docParam}` : "/tests";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Upload & AI Analysis</h1>
          <p className="text-slate-600">Upload a lab report, check what we read, then get a plain-language explanation.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {docParam && <Button variant="secondary" onClick={startOver}><RotateCcw className="h-4 w-4" />Upload another</Button>}
          <Link href={centresHref} className={buttonVariants({ variant: "secondary" })}><MapPin className="h-4 w-4" />Find tests & centres</Link>
        </div>
      </div>

      {!docParam ? (
        <>
          <Card>
            <CardContent className="space-y-4 pt-5">
              <p className="text-sm font-medium text-slate-700">1. Upload your lab report</p>
              <UploadDropzone file={file} onFile={setFile} onUpload={upload} uploading={uploading} progress={progress} />
              {uploadError && <Alert tone="error">{uploadError}</Alert>}
              {file && <DocumentPreview file={file} />}
            </CardContent>
          </Card>
          <AnalysisTeaser attached={!!file} />
        </>
      ) : (
        <>
          {error && <Alert tone="error">{error}</Alert>}
          {!doc ? <Skeleton className="h-24" /> : (
            <Card>
              <CardContent className="space-y-3 pt-5">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium text-slate-900">{doc.original_filename}</p>
                  <DocStatusBadge status={currentStatus ?? doc.status} />
                  <span className="text-sm text-slate-500">Lab report · {doc.pages} page(s)</span>
                </div>
                <ProcessingStatus status={currentStatus ?? doc.status} message={doc.status_message} onRetry={retry} />
              </CardContent>
            </Card>
          )}
          {doc && (
            <>
              {extraction && <VerificationTable extraction={extraction} onUpdated={setExtraction} focusParamId={focusParam} />}
              <AnalysisPanel doc={extraction?.document ?? doc} focusParamId={focusParam}
                onAnalyzed={() => extraction && setExtraction({ ...extraction, document: { ...extraction.document, status: "ANALYZED", has_analysis: true } })} />
              {verified && (
                <Card className="border-brand-100 bg-brand-50/50">
                  <CardContent className="flex flex-col gap-3 pt-5 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-start gap-3">
                      <MapPin className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" aria-hidden />
                      <div>
                        <p className="font-semibold text-slate-900">Need a test or a re-test?</p>
                        <p className="text-sm text-slate-600">Find diagnostic centres near you for the tests on this report.</p>
                      </div>
                    </div>
                    <Link href={centresHref} className={buttonVariants({ className: "w-full sm:w-auto" })}>
                      Go to Tests & Centres<ArrowRight className="h-4 w-4" />
                    </Link>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

export default function AnalysisPage() {
  return <Suspense fallback={<Skeleton className="h-64" />}><AnalysisInner /></Suspense>;
}
