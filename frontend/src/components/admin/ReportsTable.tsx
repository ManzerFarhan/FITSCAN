"use client";
import Link from "next/link";
import { Table } from "@/components/admin/ui";
import { DocStatusBadge } from "@/components/ui/badges";
import { CATEGORY_LABELS } from "@/lib/constants";
import type { AdminDocument } from "@/lib/types";
import { formatBytes, formatDate } from "@/lib/utils";

/** Reports list used on the Reports page and on a client's page. Rows open the report details. */
export function ReportsTable({ docs, showOwner }: { docs: AdminDocument[]; showOwner?: boolean }) {
  return (
    <Table head={<tr>{showOwner && <th className="py-2 pr-3">Client</th>}<th className="py-2 pr-3">Report</th><th className="pr-3">Status</th>
      <th className="pr-3">Type</th><th className="pr-3 text-right">Tests read</th><th className="pr-3">Uploaded</th></tr>}>
      {docs.map((d) => (
        <tr key={d.id} className="align-top hover:bg-slate-50">
          {showOwner && (
            <td className="py-2.5 pr-3">
              {d.user_id ? <Link href={`/admin/clients/${d.user_id}`} className="text-brand-700 hover:underline">{d.owner}</Link>
                : <span className="text-slate-500">Guest</span>}
            </td>
          )}
          <td className="py-2.5 pr-3">
            <Link href={`/admin/reports/${d.id}`} className="font-medium text-slate-900 hover:text-brand-700">{d.filename}</Link>
            <span className="block text-xs text-slate-500">{d.pages} page{d.pages === 1 ? "" : "s"} · {formatBytes(d.size_bytes)}{d.lab_name && ` · ${d.lab_name}`}</span>
            {d.status === "FAILED" && d.status_message && <span className="block text-xs text-red-700">{d.status_message}</span>}
          </td>
          <td className="pr-3 pt-2.5"><DocStatusBadge status={d.status} /></td>
          <td className="pr-3 pt-2.5">{d.category ? CATEGORY_LABELS[d.category] ?? d.category : "-"}</td>
          <td className="pr-3 pt-2.5 text-right tabular-nums">
            {d.parameters}
            {d.unrecognised > 0 && <span className="block text-xs text-amber-700">{d.unrecognised} not recognised</span>}
          </td>
          <td className="pr-3 pt-2.5">{formatDate(d.uploaded_at, true)}</td>
        </tr>
      ))}
      {!docs.length && <tr><td colSpan={showOwner ? 6 : 5} className="py-6 text-center text-slate-500">No reports.</td></tr>}
    </Table>
  );
}
