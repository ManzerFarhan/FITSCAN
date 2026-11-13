"use client";
import { UserMinus, UserPlus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { ConfirmDialog, LoadState, PageHeader, RoleBadge, Table, useAdminAction, useAdminData, useIsOwner } from "@/components/admin/ui";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, PasswordInput } from "@/components/ui/form";
import { Alert } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import type { AdminTeamMember } from "@/lib/types";
import { formatDate, timeAgo } from "@/lib/utils";

export default function AdminTeamPage() {
  const isOwner = useIsOwner();
  const me = useAuth().user;
  const { data, error, loading, reload } = useAdminData<AdminTeamMember[]>("/admin/admins");
  const add = useAdminAction();
  const remove = useAdminAction();
  const [form, setForm] = useState({ email: "", full_name: "", password: "" });
  const [done, setDone] = useState<string | null>(null);
  const [toRemove, setToRemove] = useState<AdminTeamMember | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setDone(null);
    const r = await add.run<{ email: string; created: boolean }>("/admin/admins", {
      method: "POST", json: { email: form.email, full_name: form.full_name || null, password: form.password || null },
    });
    if (r) {
      setDone(r.created ? `Created a new admin account for ${r.email}. Share the password with them privately.` : `${r.email} now has admin access.`);
      setForm({ email: "", full_name: "", password: "" });
      void reload();
    }
  };

  return (
    <>
      <PageHeader title="Admin team" description="People who can open this panel." />
      <div className="grid gap-5 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardContent className="p-4">
            <LoadState error={error} loading={loading && !data} />
            {data && (
              <Table head={<tr><th className="py-2 pr-3">Admin</th><th className="pr-3">Role</th><th className="pr-3">Last active</th><th className="pr-3">Since</th><th /></tr>}>
                {data.map((a) => (
                  <tr key={a.email}>
                    <td className="py-2.5 pr-3">
                      {a.id ? <Link href={`/admin/clients/${a.id}`} className="font-medium text-slate-900 hover:text-brand-700">{a.full_name || a.email}</Link>
                        : <span className="font-medium text-slate-900">{a.email}</span>}
                      <span className="block text-xs text-slate-500">{a.pending ? "Hasn't registered yet" : a.full_name ? a.email : ""}</span>
                    </td>
                    <td className="pr-3"><RoleBadge role={a.role} /></td>
                    <td className="pr-3">{a.last_login_at ? timeAgo(a.last_login_at) : "-"}</td>
                    <td className="pr-3">{a.created_at ? formatDate(a.created_at) : "-"}</td>
                    <td className="text-right">
                      {isOwner && a.role === "ADMIN" && a.id !== me?.id && (
                        <Button variant="ghost" size="sm" onClick={() => setToRemove(a)}><UserMinus className="h-4 w-4" />Remove</Button>
                      )}
                    </td>
                  </tr>
                ))}
              </Table>
            )}
            <div className="mt-4 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
              <p><b>Owner</b> - everything: view all client data, suspend, reset passwords, delete clients and reports, manage the admin team.
                Set by the <code>ADMIN_EMAILS</code> server setting, so it can&apos;t be removed from here.</p>
              <p className="mt-1"><b>Admin</b> - view all clients and reports, open original files, read reports again, suspend and reactivate clients.</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Add an admin</CardTitle>
            <CardDescription>{isOwner ? "Give an existing account admin access, or create a new admin account." : "Only the owner can add or remove admins."}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-3">
              <Field label="Email" htmlFor="adm-email">
                <Input id="adm-email" type="email" required disabled={!isOwner} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </Field>
              <Field label="Full name (new accounts)" htmlFor="adm-name">
                <Input id="adm-name" disabled={!isOwner} value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
              </Field>
              <Field label="Password (only to create a new account)" htmlFor="adm-pw" hint="At least 8 characters. Leave empty if the person already has a FITSCAN account.">
                <PasswordInput id="adm-pw" minLength={8} disabled={!isOwner} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="new-password" />
              </Field>
              {add.error && <Alert tone="error">{add.error}</Alert>}
              {done && <Alert tone="success">{done}</Alert>}
              <Button type="submit" className="w-full" disabled={!isOwner || add.busy}><UserPlus className="h-4 w-4" />Add admin</Button>
            </form>
          </CardContent>
        </Card>
      </div>
      <ConfirmDialog open={!!toRemove} onClose={() => { setToRemove(null); remove.clearError(); }} busy={remove.busy} error={remove.error}
        title="Remove admin access?" confirmLabel="Remove access" danger
        onConfirm={async () => { if (toRemove?.id && await remove.run(`/admin/admins/${toRemove.id}`, { method: "DELETE" }) !== null) { setToRemove(null); void reload(); } }}>
        <p>{toRemove?.email} will keep their FITSCAN account but won&apos;t be able to open the admin panel.</p>
      </ConfirmDialog>
    </>
  );
}
