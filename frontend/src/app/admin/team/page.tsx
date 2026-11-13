"use client";
import { Check, Copy, KeyRound, Minus, ShieldCheck, UserCheck, UserMinus, UserPlus, Wand2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { ConfirmDialog, LoadState, PageHeader, RoleBadge, Table, useAdminAction, useAdminData, useIsOwner } from "@/components/admin/ui";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, PasswordInput } from "@/components/ui/form";
import { Alert, Dialog, Spinner } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import type { AdminTeamMember } from "@/lib/types";
import { cn, formatDate, timeAgo } from "@/lib/utils";

const PERMISSIONS: [string, boolean, boolean][] = [  // [what, owner, admin]
  ["See every client, their profile and reports", true, true],
  ["Open and download original report files", true, true],
  ["Read a report again", true, true],
  ["Suspend and reactivate clients", true, true],
  ["See the activity log, dataset and system pages", true, true],
  ["Reset a client's password", true, false],
  ["Delete clients and reports", true, false],
  ["Add and remove admins", true, false],
  ["Send the weekly email now", true, false],
];

function initials(name: string) {
  return name.split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((w) => w[0]!.toUpperCase()).join("");
}

export default function AdminTeamPage() {
  const isOwner = useIsOwner();
  const me = useAuth().user;
  const { data, error, loading, reload } = useAdminData<AdminTeamMember[]>("/admin/admins");
  const remove = useAdminAction();
  const [adding, setAdding] = useState(false);
  const [toRemove, setToRemove] = useState<AdminTeamMember | null>(null);

  return (
    <>
      <PageHeader title="Admin team" description="People who can open this admin panel, and what each role can do."
        actions={isOwner && <Button onClick={() => setAdding(true)}><UserPlus className="h-4 w-4" />Add admin</Button>} />
      <div className="space-y-5">
        <Card>
          <CardContent className="p-4">
            <LoadState error={error} loading={loading && !data} />
            {data && (
              <Table head={<tr><th className="py-2 pr-3">Member</th><th className="pr-3">Role</th><th className="pr-3">Last active</th><th className="pr-3">Member since</th><th className="text-right">Actions</th></tr>}>
                {data.map((a) => {
                  const label = a.full_name || a.email;
                  return (
                    <tr key={a.email}>
                      <td className="py-3 pr-3">
                        <div className="flex items-center gap-3">
                          <span className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
                            a.role === "OWNER" ? "bg-ai-50 text-ai-700" : "bg-brand-50 text-brand-800")}>{initials(label)}</span>
                          <div className="min-w-0">
                            {a.id ? <Link href={`/admin/clients/${a.id}`} className="font-medium text-slate-900 hover:text-brand-700">{label}</Link>
                              : <span className="font-medium text-slate-900">{label}</span>}
                            {a.id === me?.id && <span className="ml-2 text-xs text-slate-500">(you)</span>}
                            <span className="block truncate text-xs text-slate-500">{a.pending ? "Hasn't created a FITSCAN account yet" : a.full_name ? a.email : ""}</span>
                          </div>
                        </div>
                      </td>
                      <td className="pr-3"><RoleBadge role={a.role} /></td>
                      <td className="pr-3">{a.last_login_at ? timeAgo(a.last_login_at) : "-"}</td>
                      <td className="pr-3">{a.created_at ? formatDate(a.created_at) : "-"}</td>
                      <td className="text-right">
                        {isOwner && a.role === "ADMIN" && a.id !== me?.id
                          ? <Button variant="ghost" size="sm" onClick={() => setToRemove(a)}><UserMinus className="h-4 w-4" />Remove</Button>
                          : <span className="text-xs text-slate-400">{a.role === "OWNER" ? "Set on the server" : ""}</span>}
                      </td>
                    </tr>
                  );
                })}
              </Table>
            )}
            {data && data.length === 1 && isOwner && (
              <div className="mt-4 flex flex-col items-center gap-2 rounded-xl border border-dashed border-slate-300 p-6 text-center">
                <ShieldCheck className="h-6 w-6 text-slate-400" />
                <p className="text-sm text-slate-600">You&apos;re the only admin. Add a colleague to help review clients and reports.</p>
                <Button variant="secondary" size="sm" onClick={() => setAdding(true)}><UserPlus className="h-4 w-4" />Add admin</Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><div><CardTitle className="text-base">Roles and permissions</CardTitle>
            <CardDescription>The Owner is set by the <code className="text-xs">ADMIN_EMAILS</code> server setting, so it can&apos;t be removed from here.</CardDescription></div></CardHeader>
          <CardContent>
            <Table head={<tr><th className="py-2 pr-3">What they can do</th><th className="w-28 pr-3 text-center">Owner</th><th className="w-28 text-center">Admin</th></tr>}>
              {PERMISSIONS.map(([what, owner, admin]) => (
                <tr key={what}>
                  <td className="py-2 pr-3 text-slate-700">{what}</td>
                  {[owner, admin].map((ok, i) => (
                    <td key={i} className="pr-3 text-center">
                      {ok ? <Check className="mx-auto h-4 w-4 text-green-700" aria-label="Yes" /> : <Minus className="mx-auto h-4 w-4 text-slate-300" aria-label="No" />}
                    </td>
                  ))}
                </tr>
              ))}
            </Table>
          </CardContent>
        </Card>
      </div>

      <AddAdminDialog open={adding} onClose={() => setAdding(false)} onAdded={() => void reload()} />
      <ConfirmDialog open={!!toRemove} onClose={() => { setToRemove(null); remove.clearError(); }} busy={remove.busy} error={remove.error}
        title="Remove admin access?" confirmLabel="Remove access" danger
        onConfirm={async () => { if (toRemove?.id && await remove.run(`/admin/admins/${toRemove.id}`, { method: "DELETE" }) !== null) { setToRemove(null); void reload(); } }}>
        <p>{toRemove?.full_name || toRemove?.email} keeps their FITSCAN account but can no longer open the admin panel.</p>
      </ConfirmDialog>
    </>
  );
}

type Mode = "existing" | "new";

function makePassword() {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  const bytes = crypto.getRandomValues(new Uint32Array(14));
  return Array.from(bytes, (b) => chars[b % chars.length]).join("");
}

function AddAdminDialog({ open, onClose, onAdded }: { open: boolean; onClose: () => void; onAdded: () => void }) {
  const add = useAdminAction();
  const [mode, setMode] = useState<Mode>("existing");
  const [form, setForm] = useState({ email: "", full_name: "", password: "" });
  const [done, setDone] = useState<{ email: string; created: boolean; password?: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const close = () => { onClose(); setTimeout(() => { setDone(null); setForm({ email: "", full_name: "", password: "" }); setMode("existing"); add.clearError(); setCopied(false); }, 200); };
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const r = await add.run<{ email: string; created: boolean }>("/admin/admins", {
      method: "POST", json: { email: form.email, full_name: mode === "new" ? form.full_name || null : null, password: mode === "new" ? form.password : null },
    });
    if (r) { setDone({ ...r, password: r.created ? form.password : undefined }); onAdded(); }
  };
  const copy = async () => {
    if (!done) return;
    const site = typeof window !== "undefined" ? `${window.location.origin}/login` : "";
    await navigator.clipboard.writeText(`FITSCAN admin login\n${site}\nEmail: ${done.email}${done.password ? `\nPassword: ${done.password}` : ""}`);
    setCopied(true);
  };

  return (
    <Dialog open={open} onClose={close} title={done ? "Admin added" : "Add an admin"}>
      {done ? (
        <div className="space-y-4 text-sm">
          <div className="flex items-start gap-3 rounded-xl bg-green-50 p-4 text-green-900">
            <UserCheck className="mt-0.5 h-5 w-5 shrink-0" />
            <p><b>{done.email}</b> {done.created ? "now has a new FITSCAN account with admin access." : "now has admin access. They'll see \"Admin panel\" in their profile menu next time they log in."}</p>
          </div>
          {done.password && (
            <div className="rounded-xl border border-slate-200 p-4">
              <p className="mb-2 font-medium text-slate-900">Share these login details privately</p>
              <dl className="space-y-1 font-mono text-[13px]">
                <div className="flex gap-2"><dt className="w-20 text-slate-500">Email</dt><dd>{done.email}</dd></div>
                <div className="flex gap-2"><dt className="w-20 text-slate-500">Password</dt><dd>{done.password}</dd></div>
              </dl>
              <p className="mt-2 text-xs text-slate-500">Ask them to change the password in Profile → Settings after their first login. It isn&apos;t shown again.</p>
            </div>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={copy}>{copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}{copied ? "Copied" : "Copy login details"}</Button>
            <Button onClick={close}>Done</Button>
          </div>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-5 text-sm">
          <div role="radiogroup" aria-label="Account type" className="grid grid-cols-2 gap-2">
            {([["existing", "Existing account", "They already use FITSCAN"], ["new", "New account", "Create a login for them"]] as const).map(([v, t, d]) => (
              <button key={v} type="button" role="radio" aria-checked={mode === v} onClick={() => setMode(v)}
                className={cn("rounded-xl border p-3 text-left transition-colors",
                  mode === v ? "border-brand-600 bg-brand-50 ring-1 ring-brand-600" : "border-slate-200 hover:bg-slate-50")}>
                <span className="block font-medium text-slate-900">{t}</span>
                <span className="text-xs text-slate-500">{d}</span>
              </button>
            ))}
          </div>

          <label className="block">
            <span className="mb-1 block font-medium text-slate-800">Email address</span>
            <Input type="email" required autoFocus value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="colleague@example.com" />
            {mode === "existing" && <span className="mt-1 block text-xs text-slate-500">The email they use to log in to FITSCAN.</span>}
          </label>

          {mode === "new" && (
            <>
              <label className="block">
                <span className="mb-1 block font-medium text-slate-800">Full name</span>
                <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="e.g. Priya Sharma" />
              </label>
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <label htmlFor="new-admin-pw" className="font-medium text-slate-800">Password</label>
                  <button type="button" onClick={() => setForm({ ...form, password: makePassword() })} className="inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:underline">
                    <Wand2 className="h-3.5 w-3.5" />Generate a strong one
                  </button>
                </div>
                <PasswordInput id="new-admin-pw" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="new-password" />
                <span className="mt-1 block text-xs text-slate-500">At least 8 characters. You&apos;ll be able to copy it on the next screen.</span>
              </div>
            </>
          )}

          <div className="flex items-start gap-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
            <KeyRound className="mt-0.5 h-4 w-4 shrink-0" />
            <p>Admins can see every client&apos;s data and reports, read reports again and suspend clients. They can&apos;t delete anything, reset passwords or manage admins.</p>
          </div>
          {add.error && <Alert tone="error">{add.error}</Alert>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={close}>Cancel</Button>
            <Button type="submit" disabled={add.busy}>{add.busy ? <Spinner /> : <UserPlus className="h-4 w-4" />}{mode === "new" ? "Create admin account" : "Give admin access"}</Button>
          </div>
        </form>
      )}
    </Dialog>
  );
}
