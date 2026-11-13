"use client";
import { Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { LoadState, PageHeader, Pager, Table, useAdminData } from "@/components/admin/ui";
import { Badge } from "@/components/ui/badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/form";
import type { AdminAuditRow, Paged } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const SIZE = 50;
const pretty = (a: string) => a.replace(/_/g, " ").toLowerCase();

/** Audit trail: client actions (uploads, confirmations, deletions) and every admin action. */
export default function AdminActivityPage() {
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [action, setAction] = useState("");
  const [page, setPage] = useState(0);
  const params = new URLSearchParams({ ...(query && { q: query }), ...(action && { action }) });
  const { data, error, loading } = useAdminData<Paged<AdminAuditRow> & { actions: string[] }>(`/admin/audit?${params}&limit=${SIZE}&offset=${page * SIZE}`);

  return (
    <>
      <PageHeader title="Activity log" description="Who did what and when - client actions and every admin view or change. Newest first." />
      <Card>
        <CardContent className="space-y-4 p-4">
          <div className="flex flex-wrap gap-2">
            <form className="flex min-w-[260px] flex-1 gap-2" onSubmit={(e) => { e.preventDefault(); setPage(0); setQuery(q.trim()); }}>
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by email or description" aria-label="Search activity" />
              <Button type="submit" variant="secondary"><Search className="h-4 w-4" />Search</Button>
            </form>
            <Select aria-label="Action" value={action} onChange={(e) => { setAction(e.target.value); setPage(0); }} className="w-auto">
              <option value="">All actions</option>
              {data?.actions.map((a) => <option key={a} value={a}>{pretty(a)}</option>)}
            </Select>
          </div>
          <LoadState error={error} loading={loading && !data} />
          {data && (
            <>
              <Table head={<tr><th className="py-2 pr-3">When</th><th className="pr-3">Who</th><th className="pr-3">Action</th><th>Details</th></tr>}>
                {data.items.map((a, i) => (
                  <tr key={i}>
                    <td className="whitespace-nowrap py-2 pr-3 text-slate-600">{formatDate(a.at, true)}</td>
                    <td className="pr-3">{a.user_id ? <Link href={`/admin/clients/${a.user_id}`} className="text-brand-700 hover:underline">{a.who}</Link> : <span className="text-slate-500">{a.who}</span>}</td>
                    <td className="pr-3"><Badge className={a.action.startsWith("ADMIN_") ? "border-ai-100 bg-ai-50 text-ai-700" : "border-slate-200 bg-slate-50 text-slate-700"}>{pretty(a.action)}</Badge></td>
                    <td>
                      {a.label ?? "-"}
                      {a.entity === "user" && a.entity_id && a.action.startsWith("ADMIN_") && a.action !== "ADMIN_DELETE_USER" &&
                        <Link href={`/admin/clients/${a.entity_id}`} className="ml-2 text-xs text-brand-700 hover:underline">open client</Link>}
                      {a.entity === "document" && a.entity_id && !a.action.includes("DELETE") &&
                        <Link href={`/admin/reports/${a.entity_id}`} className="ml-2 text-xs text-brand-700 hover:underline">open report</Link>}
                    </td>
                  </tr>
                ))}
                {!data.items.length && <tr><td colSpan={4} className="py-6 text-center text-slate-500">No activity found.</td></tr>}
              </Table>
              <Pager total={data.total} page={page} size={SIZE} onPage={setPage} />
            </>
          )}
        </CardContent>
      </Card>
    </>
  );
}
