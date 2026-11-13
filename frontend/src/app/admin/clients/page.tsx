"use client";
import { Download, Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AccountBadge, LoadState, PageHeader, Pager, RoleBadge, Table, useAdminData } from "@/components/admin/ui";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/form";
import { API_BASE } from "@/lib/api";
import type { AdminClient, Paged } from "@/lib/types";
import { formatDate, timeAgo } from "@/lib/utils";

const SIZE = 25;

export default function AdminClientsPage() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [role, setRole] = useState("");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(0);

  const params = new URLSearchParams({ sort, ...(query && { q: query }), ...(status && { status }), ...(role && { role }) });
  const { data, error, loading } = useAdminData<Paged<AdminClient>>(`/admin/users?${params}&limit=${SIZE}&offset=${page * SIZE}`);
  const reset = (fn: () => void) => { fn(); setPage(0); };

  return (
    <>
      <PageHeader title="Clients" description="Everyone with a FITSCAN account. Click a row for full details, reports and actions."
        actions={<a href={`${API_BASE}/admin/users.csv?${params}`} className="inline-flex h-8 items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-800 hover:bg-slate-50"><Download className="h-4 w-4" />Export CSV</a>} />
      <Card>
        <CardContent className="space-y-4 p-4">
          <div className="flex flex-wrap gap-2">
            <form className="flex min-w-[260px] flex-1 gap-2" onSubmit={(e) => { e.preventDefault(); reset(() => setQuery(q.trim())); }}>
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, email, phone or city" aria-label="Search clients" />
              <Button type="submit" variant="secondary"><Search className="h-4 w-4" />Search</Button>
            </form>
            <Select aria-label="Account status" value={status} onChange={(e) => reset(() => setStatus(e.target.value))} className="w-auto">
              <option value="">All accounts</option><option value="active">Active</option><option value="suspended">Suspended</option>
            </Select>
            <Select aria-label="Role" value={role} onChange={(e) => reset(() => setRole(e.target.value))} className="w-auto">
              <option value="">Everyone</option><option value="admin">Admins only</option>
            </Select>
            <Select aria-label="Sort" value={sort} onChange={(e) => reset(() => setSort(e.target.value))} className="w-auto">
              <option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="name">Name A-Z</option>
              <option value="reports">Most reports</option><option value="last_active">Recently active</option>
            </Select>
          </div>
          {query && <p className="text-sm text-slate-600">Results for &quot;{query}&quot; <button className="text-brand-700 hover:underline" onClick={() => { setQ(""); reset(() => setQuery("")); }}>Clear</button></p>}
          <LoadState error={error} loading={loading && !data} />
          {data && (
            <>
              <Table head={<tr><th className="py-2 pr-3">Client</th><th className="hidden pr-3 md:table-cell">Phone</th><th className="hidden pr-3 lg:table-cell">City</th><th className="pr-3 text-right">Reports</th>
                <th className="hidden pr-3 md:table-cell">Last active</th><th className="hidden pr-3 lg:table-cell">Joined</th><th>Status</th></tr>}>
                {data.items.map((c) => (
                  <tr key={c.id} onClick={() => router.push(`/admin/clients/${c.id}`)} className="cursor-pointer hover:bg-slate-50">
                    <td className="py-2.5 pr-3">
                      <Link href={`/admin/clients/${c.id}`} className="break-all font-medium text-slate-900 hover:text-brand-700" onClick={(e) => e.stopPropagation()}>{c.full_name || c.email}</Link>
                      {c.full_name && <span className="block break-all text-xs text-slate-500">{c.email}</span>}
                    </td>
                    <td className="hidden pr-3 md:table-cell">{c.phone || "-"}</td>
                    <td className="hidden pr-3 lg:table-cell">{c.preferred_city || "-"}</td>
                    <td className="pr-3 text-right tabular-nums">{c.documents}</td>
                    <td className="hidden pr-3 md:table-cell">{c.last_login_at ? timeAgo(c.last_login_at) : "-"}</td>
                    <td className="hidden pr-3 lg:table-cell">{formatDate(c.created_at)}</td>
                    <td><div className="flex flex-wrap gap-1"><AccountBadge disabledAt={c.disabled_at} />{c.role !== "USER" && <RoleBadge role={c.role} />}</div></td>
                  </tr>
                ))}
                {!data.items.length && <tr><td colSpan={7} className="py-6 text-center text-slate-500">No clients found.</td></tr>}
              </Table>
              <Pager total={data.total} page={page} size={SIZE} onPage={setPage} />
            </>
          )}
        </CardContent>
      </Card>
    </>
  );
}
