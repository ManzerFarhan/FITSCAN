"use client";
import { ArrowLeft, Ban, CheckCircle2, KeyRound, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { ReportsTable } from "@/components/admin/ReportsTable";
import { AccountBadge, ConfirmDialog, LoadState, PageHeader, RoleBadge, useAdminAction, useAdminData, useIsOwner } from "@/components/admin/ui";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import type { AdminClientDetail } from "@/lib/types";
import { formatDate } from "@/lib/utils";

type Pending = "suspend" | "reactivate" | "reset" | "delete" | null;

export default function AdminClientPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const me = useAuth().user;
  const isOwner = useIsOwner();
  const { data, error, loading, reload } = useAdminData<AdminClientDetail>(`/admin/users/${id}`);
  const action = useAdminAction();
  const [pending, setPending] = useState<Pending>(null);
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const u = data?.user;
  const self = u?.id === me?.id;

  const confirm = async () => {
    if (pending === "suspend" || pending === "reactivate") {
      if (await action.run(`/admin/users/${id}/${pending}`, { method: "POST" })) { setPending(null); void reload(); }
    } else if (pending === "reset") {
      const r = await action.run<{ temporary_password: string }>(`/admin/users/${id}/reset-password`, { method: "POST" });
      if (r) { setPending(null); setTempPassword(r.temporary_password); }
    } else if (pending === "delete") {
      if (await action.run(`/admin/users/${id}`, { method: "DELETE" }) !== null) router.push("/admin/clients");
    }
  };

  const rows: [string, string | number | null | undefined][] = u ? [
    ["Email", u.email], ["Phone", u.phone], ["Gender", u.gender], ["Date of birth", u.dob && formatDate(u.dob)],
    ["City", u.preferred_city], ["Address", u.address], ["Height", u.height_cm && `${u.height_cm} cm`],
    ["Weight", u.weight_kg && `${u.weight_kg} kg`], ["Keeps data", u.retention_days ? `${u.retention_days} days` : "Until deleted"],
    ["Joined", formatDate(u.created_at, true)], ["Last login", u.last_login_at ? formatDate(u.last_login_at, true) : "-"],
  ] : [];

  return (
    <>
      <Link href="/admin/clients" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-600 hover:text-brand-700"><ArrowLeft className="h-4 w-4" />All clients</Link>
      <LoadState error={error} loading={loading && !data} />
      {u && data && (
        <>
          <PageHeader title={u.full_name || u.email} description={u.full_name ? u.email : undefined}
            actions={!self && (
              <>
                {u.disabled_at
                  ? <Button variant="secondary" size="sm" onClick={() => setPending("reactivate")}><CheckCircle2 className="h-4 w-4" />Reactivate</Button>
                  : u.role !== "OWNER" && <Button variant="secondary" size="sm" onClick={() => setPending("suspend")}><Ban className="h-4 w-4" />Suspend</Button>}
                {isOwner && <Button variant="secondary" size="sm" onClick={() => setPending("reset")}><KeyRound className="h-4 w-4" />Reset password</Button>}
                {isOwner && u.role !== "OWNER" && <Button variant="danger" size="sm" onClick={() => setPending("delete")}><Trash2 className="h-4 w-4" />Delete account</Button>}
              </>
            )} />
          {tempPassword && (
            <Alert tone="success" title="Temporary password set" className="mb-4" onClose={() => setTempPassword(null)}>
              Give this to the client privately: <code className="rounded bg-white px-1.5 py-0.5 font-mono">{tempPassword}</code>. They have been signed out
              everywhere and should change it in Profile → Settings after logging in. It won&apos;t be shown again.
            </Alert>
          )}
          <div className="grid gap-5 xl:grid-cols-3">
            <Card className="xl:col-span-1">
              <CardHeader className="flex-row items-center justify-between gap-2">
                <CardTitle className="text-base">Profile</CardTitle>
                <div className="flex gap-1"><AccountBadge disabledAt={u.disabled_at} /><RoleBadge role={u.role} /></div>
              </CardHeader>
              <CardContent>
                <dl className="space-y-2 text-sm">
                  {rows.map(([k, v]) => (
                    <div key={k} className="flex gap-3"><dt className="w-28 shrink-0 text-slate-500">{k}</dt><dd className="min-w-0 break-words text-slate-900">{v || "-"}</dd></div>
                  ))}
                </dl>
              </CardContent>
            </Card>
            <div className="space-y-5 xl:col-span-2">
              <Card>
                <CardHeader><CardTitle className="text-base">Reports ({data.documents.length})</CardTitle></CardHeader>
                <CardContent><ReportsTable docs={data.documents} /></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-base">Recent activity</CardTitle></CardHeader>
                <CardContent>
                  <ul className="divide-y divide-slate-100 text-sm">
                    {data.activity.map((a, i) => (
                      <li key={i} className="flex justify-between gap-3 py-2">
                        <span>{a.label || a.action.replace(/_/g, " ").toLowerCase()}</span>
                        <span className="shrink-0 text-slate-500">{formatDate(a.at, true)}</span>
                      </li>
                    ))}
                    {!data.activity.length && <li className="py-2 text-slate-500">No activity recorded.</li>}
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
          <ConfirmDialog open={pending !== null} onClose={() => { setPending(null); action.clearError(); }} busy={action.busy} error={action.error}
            onConfirm={confirm} danger={pending === "delete" || pending === "suspend"}
            title={{ suspend: "Suspend this account?", reactivate: "Reactivate this account?", reset: "Reset password?", delete: "Delete this account?" }[pending ?? "suspend"]}
            confirmLabel={{ suspend: "Suspend", reactivate: "Reactivate", reset: "Set temporary password", delete: "Delete permanently" }[pending ?? "suspend"]}
            confirmText={pending === "delete" ? "DELETE" : undefined}>
            {pending === "suspend" && <p>{u.email} will be signed out immediately and won&apos;t be able to log in until reactivated. Their data is kept.</p>}
            {pending === "reactivate" && <p>{u.email} will be able to log in again.</p>}
            {pending === "reset" && <p>A new temporary password will be generated for {u.email}. Their current password stops working and they are signed out everywhere.</p>}
            {pending === "delete" && <p>This permanently deletes {u.email}, all {data.documents.length} report(s), results and analyses. This can&apos;t be undone.</p>}
          </ConfirmDialog>
        </>
      )}
    </>
  );
}
