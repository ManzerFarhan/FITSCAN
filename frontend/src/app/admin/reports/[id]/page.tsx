"use client";
import { ArrowLeft, Download, ExternalLink, RotateCcw, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { ConfirmDialog, LoadState, PageHeader, StatTile, Table, useAdminAction, useAdminData, useIsOwner } from "@/components/admin/ui";
import { DocStatusBadge, StatusBadge } from "@/components/ui/badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert } from "@/components/ui/misc";
import { API_BASE } from "@/lib/api";
import { CATEGORY_LABELS, ISSUE_LABELS } from "@/lib/constants";
import type { AdminDocumentDetail } from "@/lib/types";
import { formatBytes, formatDate } from "@/lib/utils";

const LINK_BTN = "inline-flex h-8 items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-800 hover:bg-slate-50";

export default function AdminReportPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const isOwner = useIsOwner();
  const { data: d, error, loading, reload } = useAdminData<AdminDocumentDetail>(`/admin/documents/${id}`);
  const action = useAdminAction();
  const [pending, setPending] = useState<"reprocess" | "delete" | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const confirm = async () => {
    if (pending === "reprocess") {
      if (await action.run(`/admin/documents/${id}/reprocess`, { method: "POST" })) {
        setPending(null);
        setNotice("Reading again - refresh in a minute to see the new results.");
        void reload();
      }
    } else if (pending === "delete") {
      if (await action.run(`/admin/documents/${id}`, { method: "DELETE" }) !== null) {
        router.push(d?.user_id ? `/admin/clients/${d.user_id}` : "/admin/reports");
      }
    }
  };

  const fileUrl = `${API_BASE}/admin/documents/${id}/file`;
  const meta: [string, string | null | undefined][] = d ? [
    ["Client", d.owner], ["Lab", d.lab_name], ["Report type", d.category ? CATEGORY_LABELS[d.category] ?? d.category : null],
    ["Report date", d.report_date && formatDate(d.report_date)], ["Collected", d.collected_date && formatDate(d.collected_date)],
    ["Patient name (on report)", d.patient_name], ["Doctor", d.doctor_name], ["Uploaded", formatDate(d.uploaded_at, true)],
    ["File", `${d.pages} page${d.pages === 1 ? "" : "s"} · ${formatBytes(d.size_bytes)} · ${d.mime}`], ["Read with", d.engine],
  ] : [];

  return (
    <>
      <Link href="/admin/reports" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-600 hover:text-brand-700"><ArrowLeft className="h-4 w-4" />All reports</Link>
      <LoadState error={error} loading={loading && !d} />
      {d && (
        <>
          <PageHeader title={d.filename}
            actions={<>
              <a href={fileUrl} target="_blank" rel="noreferrer" className={LINK_BTN}><ExternalLink className="h-4 w-4" />Open original</a>
              <a href={`${fileUrl}?download=true`} className={LINK_BTN}><Download className="h-4 w-4" />Download</a>
              <Button variant="secondary" size="sm" onClick={() => setPending("reprocess")}><RotateCcw className="h-4 w-4" />Read again</Button>
              {isOwner && <Button variant="danger" size="sm" onClick={() => setPending("delete")}><Trash2 className="h-4 w-4" />Delete</Button>}
            </>} />
          {notice && <Alert tone="info" className="mb-4" onClose={() => setNotice(null)}>{notice}</Alert>}
          {d.status === "FAILED" && <Alert tone="error" title="This report could not be read" className="mb-4">{d.status_message}</Alert>}
          <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Card><CardContent className="p-4"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">Status</p><div className="mt-2"><DocStatusBadge status={d.status} /></div></CardContent></Card>
            <StatTile label="Tests read" value={d.parameters} />
            <StatTile label="Not recognised" value={d.unrecognised} tone={d.unrecognised ? "warn" : undefined} />
            <StatTile label="Outside lab range" value={d.out_of_range} />
          </div>
          <div className="grid gap-5 xl:grid-cols-3">
            <Card>
              <CardHeader><CardTitle className="text-base">Details</CardTitle></CardHeader>
              <CardContent>
                <dl className="space-y-2 text-sm">
                  {meta.map(([k, v]) => <div key={k} className="flex gap-3"><dt className="w-32 shrink-0 text-slate-500">{k}</dt><dd className="min-w-0 break-words">{v || "-"}</dd></div>)}
                </dl>
                {!!d.warnings.length && <p className="mt-3 text-xs text-amber-700">Reader notes: {d.warnings.join(", ").replace(/_/g, " ").toLowerCase()}</p>}
              </CardContent>
            </Card>
            <Card className="xl:col-span-2">
              <CardHeader><CardTitle className="text-base">What was read ({d.results.length})</CardTitle></CardHeader>
              <CardContent>
                <Table head={<tr><th className="py-2 pr-3">Test (as printed)</th><th className="pr-3">Matched to</th><th className="pr-3 text-right">Value</th>
                  <th className="pr-3">Lab range</th><th className="pr-3">Status</th><th className="text-right">Confidence</th></tr>}>
                  {d.results.map((p) => (
                    <tr key={p.id} className="align-top">
                      <td className="py-2 pr-3">
                        {p.name_raw}
                        {!!p.issues.length && <span className="block text-xs text-amber-700">{p.issues.map((i) => ISSUE_LABELS[i] ?? i).join(" · ")}</span>}
                      </td>
                      <td className="pr-3 pt-2">{p.canonical_name ?? <span className="text-amber-700">Not recognised</span>}</td>
                      <td className="pr-3 pt-2 text-right tabular-nums">{p.value_raw ?? "-"} <span className="text-slate-500">{p.unit ?? ""}</span></td>
                      <td className="pr-3 pt-2">{p.ref_raw ?? "-"}</td>
                      <td className="pr-3 pt-2"><StatusBadge status={p.status} /></td>
                      <td className="pt-2 text-right tabular-nums">{Math.round(p.confidence * 100)}%</td>
                    </tr>
                  ))}
                  {!d.results.length && <tr><td colSpan={6} className="py-6 text-center text-slate-500">No test results were read from this report.</td></tr>}
                </Table>
              </CardContent>
            </Card>
          </div>
          <ConfirmDialog open={pending !== null} onClose={() => { setPending(null); action.clearError(); }} busy={action.busy} error={action.error}
            onConfirm={confirm} danger={pending === "delete"} confirmText={pending === "delete" ? "DELETE" : undefined}
            title={pending === "delete" ? "Delete this report?" : "Read this report again?"}
            confirmLabel={pending === "delete" ? "Delete permanently" : "Read again"}>
            {pending === "delete"
              ? <p>The file, its results and analyses will be permanently deleted for {d.owner}. This can&apos;t be undone.</p>
              : <p>FITSCAN reads the original file again with the latest reader and test dictionary. Any corrections the client made to this report will be replaced.</p>}
          </ConfirmDialog>
        </>
      )}
    </>
  );
}
