"use client";
import { RefreshCw, Search, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DocStatusBadge } from "@/components/ui/badges";
import { Input, Select } from "@/components/ui/form";
import { Alert, Dialog, Empty, Skeleton, Tabs } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import { CATEGORY_LABELS, DOCUMENT_STATUSES } from "@/lib/constants";
import type { AdminClient, AdminClientDetail, AdminDocument, AdminOverview } from "@/lib/types";
import { formatBytes, formatDate, timeAgo } from "@/lib/utils";

type Tab = "overview" | "clients" | "reports";
const PAGE = 50;

/** Admin panel - read-only view of clients and their reports. Server allows only ADMIN_EMAILS accounts. */
export default function AdminPage() {
  const { user, loading } = useAuth();
  const [tab, setTab] = useState<Tab>("overview");
  const [openClient, setOpenClient] = useState<string | null>(null);

  if (loading) return <Skeleton className="h-64" />;
  if (!user?.is_admin) {
    return (
      <Empty icon={<ShieldCheck className="h-8 w-8" />} title="Admins only">
        {user ? "Your account doesn't have admin access." : "Log in with an admin account to open this page."}
        {!user && <div className="mt-4"><Link href="/login?next=/admin" className={buttonVariants()}>Log in</Link></div>}
      </Empty>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Admin</h1>
          <p className="text-sm text-slate-500">Clients, their reports and how well reports are being read. Read-only.</p>
        </div>
        <Tabs<Tab> value={tab} onChange={setTab}
          tabs={[{ value: "overview", label: "Overview" }, { value: "clients", label: "Clients" }, { value: "reports", label: "Reports" }]} />
      </div>
      {tab === "overview" && <Overview />}
      {tab === "clients" && <Clients onOpen={setOpenClient} />}
      {tab === "reports" && <Reports onOpen={setOpenClient} />}
      <ClientDialog id={openClient} onClose={() => setOpenClient(null)} />
    </div>
  );
}

function useLoad<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    if (!path) return;
    setError(null);
    try { setData(await api<T>(path)); } catch (e) { setError(e instanceof ApiError ? e.message : "Couldn't load."); }
  }, [path]);
  useEffect(() => { setData(null); void load(); }, [load]);
  return { data, error, reload: load };
}

function Stat({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <Card><CardContent className="p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </CardContent></Card>
  );
}

function Overview() {
  const { data, error, reload } = useLoad<AdminOverview>("/admin/overview");
  if (error) return <Alert tone="error">{error}</Alert>;
  if (!data) return <Skeleton className="h-40" />;
  return (
    <div className="space-y-5">
      <div className="flex justify-end"><Button variant="secondary" size="sm" onClick={reload}><RefreshCw className="h-4 w-4" />Refresh</Button></div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Clients" value={data.users} sub={`+${data.users_7d} this week`} />
        <Stat label="Reports" value={data.documents} sub={`+${data.documents_7d} this week`} />
        <Stat label="Failed reads" value={data.failed} sub="reports that could not be read" />
        <Stat label="Guests now" value={data.guests_active} sub="active guest sessions (24 h)" />
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base">Reports by status</CardTitle></CardHeader>
          <CardContent>
            <ul className="divide-y divide-slate-100 text-sm">
              {Object.entries(data.by_status).sort((a, b) => b[1] - a[1]).map(([s, n]) => (
                <li key={s} className="flex items-center justify-between py-2"><DocStatusBadge status={s as never} /><span className="font-medium">{n}</span></li>
              ))}
              {!Object.keys(data.by_status).length && <li className="py-2 text-slate-500">No reports yet.</li>}
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Test names not recognised</CardTitle>
            <p className="text-xs text-slate-500">Printed names that matched nothing in the test dictionary - candidates to add.</p>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-slate-100 text-sm">
              {data.unrecognised_tests.map((t) => (
                <li key={t.name} className="flex justify-between gap-3 py-2"><span className="truncate">{t.name}</span><span className="text-slate-500">{t.count}x</span></li>
              ))}
              {!data.unrecognised_tests.length && <li className="py-2 text-slate-500">None - every test name was recognised.</li>}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Clients({ onOpen }: { onOpen: (id: string) => void }) {
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const { data, error } = useLoad<{ total: number; items: AdminClient[] }>(
    `/admin/users?limit=${PAGE}&offset=${page * PAGE}${query ? `&q=${encodeURIComponent(query)}` : ""}`);
  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); setPage(0); setQuery(q.trim()); }}>
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, email, phone or city" aria-label="Search clients" />
          <Button type="submit"><Search className="h-4 w-4" />Search</Button>
        </form>
        {error && <Alert tone="error">{error}</Alert>}
        {!data && !error && <Skeleton className="h-40" />}
        {data && (
          <>
            <p className="text-sm text-slate-500">{data.total} client{data.total === 1 ? "" : "s"}{query && ` matching "${query}"`}</p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
                  <tr><th className="py-2 pr-3">Name</th><th className="pr-3">Email</th><th className="pr-3">Phone</th><th className="pr-3">City</th>
                    <th className="pr-3 text-right">Reports</th><th className="pr-3">Last upload</th><th>Joined</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.items.map((c) => (
                    <tr key={c.id} onClick={() => onOpen(c.id)} className="cursor-pointer hover:bg-slate-50">
                      <td className="py-2 pr-3 font-medium text-slate-900">{c.full_name || "-"}</td>
                      <td className="pr-3">{c.email}</td><td className="pr-3">{c.phone || "-"}</td><td className="pr-3">{c.preferred_city || "-"}</td>
                      <td className="pr-3 text-right">{c.documents}</td>
                      <td className="pr-3">{c.last_upload ? timeAgo(c.last_upload) : "-"}</td><td>{formatDate(c.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.total > PAGE && (
              <div className="flex items-center justify-end gap-2 text-sm">
                <Button variant="secondary" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>Previous</Button>
                <span>Page {page + 1} of {Math.ceil(data.total / PAGE)}</span>
                <Button variant="secondary" size="sm" disabled={(page + 1) * PAGE >= data.total} onClick={() => setPage((p) => p + 1)}>Next</Button>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function DocTable({ docs, showOwner, onOpen }: { docs: AdminDocument[]; showOwner?: boolean; onOpen?: (id: string) => void }) {
  if (!docs.length) return <p className="text-sm text-slate-500">No reports.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
          <tr>{showOwner && <th className="py-2 pr-3">Client</th>}<th className="py-2 pr-3">File</th><th className="pr-3">Status</th>
            <th className="pr-3">Type</th><th className="pr-3 text-right">Tests read</th><th className="pr-3">Uploaded</th></tr>
        </thead>
        <tbody className="divide-y divide-slate-100 align-top">
          {docs.map((d) => (
            <tr key={d.id}>
              {showOwner && (
                <td className="py-2 pr-3">
                  {d.user_id && onOpen ? <button className="text-brand-700 hover:underline" onClick={() => onOpen(d.user_id!)}>{d.owner}</button> : d.owner}
                </td>
              )}
              <td className="py-2 pr-3">
                <span className="font-medium text-slate-900">{d.filename}</span>
                <span className="block text-xs text-slate-500">{d.pages} page{d.pages === 1 ? "" : "s"} · {formatBytes(d.size_bytes)}{d.lab_name && ` · ${d.lab_name}`}</span>
                {d.status === "FAILED" && d.status_message && <span className="block text-xs text-red-700">{d.status_message}</span>}
              </td>
              <td className="pr-3"><DocStatusBadge status={d.status} /></td>
              <td className="pr-3">{d.category ? CATEGORY_LABELS[d.category] ?? d.category : "-"}</td>
              <td className="pr-3 text-right">{d.parameters}{d.unrecognised > 0 && <span className="block text-xs text-amber-700">{d.unrecognised} unrecognised</span>}</td>
              <td className="pr-3">{formatDate(d.uploaded_at, true)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Reports({ onOpen }: { onOpen: (id: string) => void }) {
  const [status, setStatus] = useState("");
  const { data, error } = useLoad<AdminDocument[]>(`/admin/documents${status ? `?status=${status}` : ""}`);
  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div className="flex items-center gap-2">
          <label htmlFor="st" className="text-sm text-slate-600">Status</label>
          <Select id="st" value={status} onChange={(e) => setStatus(e.target.value)} className="max-w-xs">
            <option value="">All (latest 200)</option>
            {DOCUMENT_STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ").toLowerCase()}</option>)}
          </Select>
        </div>
        {error && <Alert tone="error">{error}</Alert>}
        {!data && !error ? <Skeleton className="h-40" /> : data && <DocTable docs={data} showOwner onOpen={onOpen} />}
      </CardContent>
    </Card>
  );
}

function ClientDialog({ id, onClose }: { id: string | null; onClose: () => void }) {
  const { data, error } = useLoad<AdminClientDetail>(id ? `/admin/users/${id}` : null);
  const u = data?.user;
  const rows: [string, string | number | null | undefined][] = u ? [
    ["Email", u.email], ["Phone", u.phone], ["Gender", u.gender], ["Date of birth", u.dob && formatDate(u.dob)],
    ["City", u.preferred_city], ["Address", u.address], ["Height", u.height_cm && `${u.height_cm} cm`],
    ["Weight", u.weight_kg && `${u.weight_kg} kg`], ["Keeps data", u.retention_days ? `${u.retention_days} days` : "until deleted"],
    ["Joined", formatDate(u.created_at, true)],
  ] : [];
  return (
    <Dialog open={!!id} onClose={onClose} title={u ? u.full_name || u.email : "Client"} wide>
      {error && <Alert tone="error">{error}</Alert>}
      {!data && !error && <Skeleton className="h-40" />}
      {data && (
        <div className="space-y-6">
          <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
            {rows.map(([k, v]) => (
              <div key={k} className="flex gap-2"><dt className="w-28 shrink-0 text-slate-500">{k}</dt><dd className="text-slate-900">{v || "-"}</dd></div>
            ))}
          </dl>
          <section>
            <h3 className="mb-2 font-semibold text-slate-900">Reports ({data.documents.length})</h3>
            <DocTable docs={data.documents} />
          </section>
          <section>
            <h3 className="mb-2 font-semibold text-slate-900">Recent activity</h3>
            <ul className="divide-y divide-slate-100 text-sm">
              {data.activity.map((a, i) => (
                <li key={i} className="flex justify-between gap-3 py-1.5">
                  <span>{a.label || a.action.replace(/_/g, " ").toLowerCase()}</span>
                  <span className="shrink-0 text-slate-500">{formatDate(a.at, true)}</span>
                </li>
              ))}
              {!data.activity.length && <li className="py-1.5 text-slate-500">No activity recorded.</li>}
            </ul>
          </section>
        </div>
      )}
    </Dialog>
  );
}
