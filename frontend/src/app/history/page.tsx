"use client";
import { GitCompare } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { ComparisonSelector } from "@/components/history/ComparisonSelector";
import { ComparisonSummary } from "@/components/history/ComparisonSummary";
import { DocumentFilters, EMPTY_FILTERS, type Filters } from "@/components/history/DocumentFilters";
import { DocumentList } from "@/components/history/DocumentList";
import { PrevCurrentCards } from "@/components/history/PrevCurrentCards";
import { TrendChart } from "@/components/history/TrendChart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Dialog, Skeleton } from "@/components/ui/misc";
import { api, ApiError } from "@/lib/api";
import type { ComparisonOut, DocumentOut } from "@/lib/types";

function HistoryInner() {
  const params = useSearchParams();
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [docs, setDocs] = useState<DocumentOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [compareMode, setCompareMode] = useState(params.get("compare") === "1");
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [toDelete, setToDelete] = useState<DocumentOut | null>(null);
  const onlyAnalysed = params.get("filter") === "analysed";

  useEffect(() => {
    const q = new URLSearchParams();
    if (filters.q) q.set("q", filters.q);
    if (filters.category) q.set("category", filters.category);
    if (filters.from) q.set("from", filters.from);
    if (filters.to) q.set("to", filters.to);
    const t = setTimeout(() => {
      api<{ items: DocumentOut[] }>(`/documents?${q}`).then((r) => setDocs(r.items))
        .catch((e) => { setDocs([]); setError(e instanceof ApiError ? e.message : "Could not load your history."); });
    }, 250);
    return () => clearTimeout(t);
  }, [filters]);

  const shown = useMemo(() => (onlyAnalysed ? docs?.filter((d) => d.has_analysis) : docs) ?? null, [docs, onlyAnalysed]);

  const compare = async () => {
    setBusy(true); setError(null);
    try {
      setComparison(await api<ComparisonOut>("/comparisons", { method: "POST", json: { document_ids: selected } }));
      setTimeout(() => document.getElementById("comparison")?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Comparison failed.");
    } finally { setBusy(false); }
  };

  const del = async () => {
    if (!toDelete) return;
    try {
      await api(`/documents/${toDelete.id}`, { method: "DELETE" });
      setDocs((d) => d?.filter((x) => x.id !== toDelete.id) ?? null);
      setSelected((s) => s.filter((x) => x !== toDelete.id));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Delete failed.");
    } finally { setToDelete(null); }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Medical History</h1>
          <p className="text-slate-600">All your lab reports, and how values change over time.</p>
        </div>
        {!compareMode && <Button variant="secondary" onClick={() => setCompareMode(true)}><GitCompare className="h-4 w-4" />Compare reports</Button>}
      </div>
      <DocumentFilters value={filters} onChange={setFilters} />
      {onlyAnalysed && <Alert tone="info">Showing documents with an AI analysis.</Alert>}
      {compareMode && <ComparisonSelector count={selected.length} busy={busy} onCompare={compare}
        onCancel={() => { setCompareMode(false); setSelected([]); }} />}
      {error && <Alert tone="error" onClose={() => setError(null)}>{error}</Alert>}
      {!shown ? <Skeleton className="h-48" /> : (
        <DocumentList docs={shown} selected={selected} compareMode={compareMode} onDelete={setToDelete}
          onToggle={(id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))} />
      )}

      {comparison && (
        <Card id="comparison">
          <CardHeader><CardTitle>Comparison of {comparison.result.documents.length} reports</CardTitle></CardHeader>
          <CardContent className="space-y-6">
            <ComparisonSummary comparison={comparison} />
            {comparison.result.compared.length === 0 ? (
              <Alert tone="info">No parameters could be matched between these reports.</Alert>
            ) : (
              <>
                <PrevCurrentCards items={comparison.result.compared} />
                <div className="grid gap-6 md:grid-cols-2">
                  {comparison.result.compared.map((c) => <TrendChart key={c.parameter_id} param={c} />)}
                </div>
              </>
            )}
            <p className="text-xs text-slate-500">{comparison.disclaimer}</p>
          </CardContent>
        </Card>
      )}

      <Dialog open={!!toDelete} onClose={() => setToDelete(null)} title="Delete document?">
        <p className="text-sm text-slate-700">
          This permanently deletes <strong>{toDelete?.original_filename}</strong>, its extracted values, analyses and chat history. This can't be undone.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setToDelete(null)}>Cancel</Button>
          <Button variant="danger" onClick={del}>Delete</Button>
        </div>
      </Dialog>
    </div>
  );
}

export default function HistoryPage() {
  return <Suspense fallback={<Skeleton className="h-64" />}><HistoryInner /></Suspense>;
}
