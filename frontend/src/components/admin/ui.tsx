"use client";
import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Badge } from "@/components/ui/badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/form";
import { Alert, Dialog, Spinner } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import type { AdminRole, DailyCount } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

/** GET an admin endpoint; `path = null` waits. Returns data, error and a reload function. */
export function useAdminData<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const load = useCallback(async () => {
    if (!path) return;
    setLoading(true);
    setError(null);
    try { setData(await api<T>(path)); } catch (e) { setError(e instanceof ApiError ? e.message : "Couldn't load."); }
    finally { setLoading(false); }
  }, [path]);
  useEffect(() => { void load(); }, [load]);
  return { data, error, loading, reload: load };
}

/** Run an admin action (POST/DELETE) with a busy flag and a readable error. */
export function useAdminAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = async <T,>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T | null> => {
    setBusy(true);
    setError(null);
    try { return await api<T>(path, init); } catch (e) { setError(e instanceof ApiError ? e.message : "Action failed."); return null; }
    finally { setBusy(false); }
  };
  return { run, busy, error, clearError: () => setError(null) };
}

export function useIsOwner(): boolean {
  return useAuth().user?.admin_role === "OWNER";
}

export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: React.ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{title}</h1>
        {description && <p className="mt-0.5 text-sm text-slate-500">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function StatTile({ label, value, sub, tone }: { label: string; value: number | string; sub?: string; tone?: "warn" }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
        <p className={cn("mt-1 text-2xl font-bold tabular-nums", tone === "warn" ? "text-red-700" : "text-slate-900")}>{value}</p>
        {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export function LoadState({ error, loading }: { error: string | null; loading?: boolean }) {
  if (error) return <Alert tone="error">{error}</Alert>;
  if (loading) return <div className="flex items-center gap-2 py-8 text-sm text-slate-500"><Spinner />Loading...</div>;
  return null;
}

export function Pager({ total, page, size, onPage }: { total: number; page: number; size: number; onPage: (p: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / size));
  if (total <= size) return <p className="text-xs text-slate-500">{total} result{total === 1 ? "" : "s"}</p>;
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
      <p className="text-xs text-slate-500">{page * size + 1}-{Math.min(total, (page + 1) * size)} of {total}</p>
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" disabled={page === 0} onClick={() => onPage(page - 1)}>Previous</Button>
        <span className="text-slate-600">Page {page + 1} of {pages}</span>
        <Button variant="secondary" size="sm" disabled={page + 1 >= pages} onClick={() => onPage(page + 1)}>Next</Button>
      </div>
    </div>
  );
}

const ROLE_STYLE: Record<AdminRole, { t: string; c: string }> = {
  OWNER: { t: "Owner", c: "border-ai-100 bg-ai-50 text-ai-700" },
  ADMIN: { t: "Admin", c: "border-brand-200 bg-brand-50 text-brand-800" },
  USER: { t: "Client", c: "border-slate-200 bg-slate-50 text-slate-700" },
};
export function RoleBadge({ role }: { role: AdminRole }) {
  const s = ROLE_STYLE[role] ?? ROLE_STYLE.USER;
  return <Badge className={s.c}>{s.t}</Badge>;
}

export function AccountBadge({ disabledAt }: { disabledAt: string | null }) {
  return disabledAt
    ? <Badge className="border-red-200 bg-red-50 text-red-800" title={`Suspended ${formatDate(disabledAt, true)}`}>Suspended</Badge>
    : <Badge className="border-green-200 bg-green-50 text-green-800">Active</Badge>;
}

/** Confirmation for destructive actions. `confirmText` makes the admin type a word (e.g. DELETE) first. */
export function ConfirmDialog({ open, title, children, confirmLabel, danger, confirmText, busy, error, onConfirm, onClose }: {
  open: boolean; title: string; children: React.ReactNode; confirmLabel: string; danger?: boolean; confirmText?: string;
  busy?: boolean; error?: string | null; onConfirm: () => void; onClose: () => void;
}) {
  const [typed, setTyped] = useState("");
  useEffect(() => { if (!open) setTyped(""); }, [open]);
  const ready = !confirmText || typed.trim().toUpperCase() === confirmText;
  return (
    <Dialog open={open} onClose={onClose} title={title}>
      <div className="space-y-4 text-sm text-slate-700">
        {children}
        {confirmText && (
          <label className="block">
            <span className="text-slate-600">Type <b>{confirmText}</b> to confirm</span>
            <Input className="mt-1" value={typed} onChange={(e) => setTyped(e.target.value)} autoFocus />
          </label>
        )}
        {error && <Alert tone="error">{error}</Alert>}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button variant={danger ? "danger" : "default"} disabled={!ready || busy} onClick={onConfirm}>
            {busy && <Spinner />}{confirmLabel}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

const BAR = "#0d9488"; // brand-600; validated (lightness, chroma, contrast vs surface)
const AXIS = { fontSize: 11, fill: "#64748b" };

/** One series of daily counts - a single bar per day, the card title names the series (no legend needed). */
export function DailyBars({ data, label }: { data: DailyCount[]; label: string }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  return (
    <div>
      <p className="mb-2 text-sm text-slate-500"><span className="text-xl font-bold text-slate-900 tabular-nums">{total}</span> in the last {data.length} days</p>
      <div className="h-48" role="img" aria-label={`${label}: ${total} in the last ${data.length} days`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: 0 }} barCategoryGap={2}>
            <CartesianGrid vertical={false} stroke="#eef2f6" />
            <XAxis dataKey="date" tick={AXIS} tickLine={false} axisLine={{ stroke: "#e2e8f0" }} minTickGap={24}
              tickFormatter={(d: string) => new Date(`${d}T00:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "short" })} />
            <YAxis allowDecimals={false} tick={AXIS} tickLine={false} axisLine={false} width={28} />
            <Tooltip cursor={{ fill: "#f1f5f9" }} labelFormatter={(d) => formatDate(String(d))}
              formatter={(v) => [v as number, label]} contentStyle={{ borderRadius: 8, borderColor: "#e2e8f0", fontSize: 12 }} />
            <Bar dataKey="count" fill={BAR} radius={[4, 4, 0, 0]} maxBarSize={18} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

/** A simple table shell with consistent header styling. */
export function Table({ head, children }: { head: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">{head}</thead>
        <tbody className="divide-y divide-slate-100">{children}</tbody>
      </table>
    </div>
  );
}
