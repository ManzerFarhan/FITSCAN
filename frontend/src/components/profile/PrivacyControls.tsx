"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, PasswordInput } from "@/components/ui/form";
import { Alert, Dialog } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";

/** FR-PROF-4 privacy: view/delete docs, retention, account deletion. */
export function PrivacyControls({ user, onSaved }: { user: User; onSaved: (u: User) => void }) {
  const router = useRouter();
  const { setUser } = useAuth();
  const [retention, setRetention] = useState(user.retention_days ? String(user.retention_days) : "");
  const [msg, setMsg] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const [confirmDocs, setConfirmDocs] = useState(false);
  const [confirmAccount, setConfirmAccount] = useState(false);
  const [password, setPassword] = useState("");

  const saveRetention = async () => {
    try {
      onSaved(await api<User>("/profile", { method: "PATCH", json: { retention_days: retention ? Number(retention) : null } }));
      setMsg({ tone: "success", text: "Retention preference saved." });
    } catch (e) { setMsg({ tone: "error", text: e instanceof ApiError ? e.message : "Could not save." }); }
  };
  const deleteDocs = async () => {
    try {
      const r = await api<{ deleted: number }>("/profile/documents", { method: "DELETE" });
      setMsg({ tone: "success", text: `Deleted ${r.deleted} document(s).` });
    } catch (e) { setMsg({ tone: "error", text: e instanceof ApiError ? e.message : "Could not delete." }); }
    setConfirmDocs(false);
  };
  const deleteAccount = async () => {
    try {
      await api("/profile", { method: "DELETE", json: { password } });
      setUser(null);
      router.push("/dashboard");
    } catch (e) { setMsg({ tone: "error", text: e instanceof ApiError ? e.message : "Could not delete account." }); setConfirmAccount(false); }
  };

  return (
    <div className="space-y-6">
      {msg && <Alert tone={msg.tone} onClose={() => setMsg(null)}>{msg.text}</Alert>}
      <section className="space-y-2">
        <h3 className="font-semibold text-slate-900">Your documents</h3>
        <p className="text-sm text-slate-600">View, download or delete individual documents from <Link href="/history" className="text-brand-700 underline">History</Link>.</p>
        <Button variant="secondary" onClick={() => setConfirmDocs(true)}>Delete all my documents</Button>
      </section>
      <section className="space-y-2">
        <h3 className="font-semibold text-slate-900">Data retention</h3>
        <div className="flex flex-wrap items-end gap-2">
          <div className="w-64">
            <Field label="Automatically delete documents after" htmlFor="ret">
              <Select id="ret" value={retention} onChange={(e) => setRetention(e.target.value)}>
                <option value="">Keep until I delete them</option>
                <option value="30">30 days</option><option value="90">90 days</option><option value="365">1 year</option><option value="1095">3 years</option>
              </Select>
            </Field>
          </div>
          <Button onClick={saveRetention}>Save</Button>
        </div>
      </section>
      <section className="space-y-2">
        <h3 className="font-semibold text-red-700">Delete account</h3>
        <p className="text-sm text-slate-600">Permanently deletes your account and every document, analysis and comparison.</p>
        <Button variant="danger" onClick={() => setConfirmAccount(true)}>Delete my account</Button>
      </section>
      <section className="text-sm text-slate-600">
        <h3 className="font-semibold text-slate-900">Privacy policy (summary)</h3>
        <ul className="mt-1 list-disc space-y-1 pl-5">
          <li>Your documents are stored privately and only you can access them.</li>
          <li>Original files are served through short-lived, signed links.</li>
          <li>Guest uploads are deleted automatically after 24 hours.</li>
          <li>Only verified values (no names or addresses) are sent to the AI explanation service.</li>
          <li>Logs never contain your medical values.</li>
        </ul>
      </section>
      <Dialog open={confirmDocs} onClose={() => setConfirmDocs(false)} title="Delete all documents?">
        <p className="text-sm">This permanently deletes every document and everything derived from it.</p>
        <div className="mt-4 flex justify-end gap-2"><Button variant="secondary" onClick={() => setConfirmDocs(false)}>Cancel</Button><Button variant="danger" onClick={deleteDocs}>Delete all</Button></div>
      </Dialog>
      <Dialog open={confirmAccount} onClose={() => setConfirmAccount(false)} title="Delete your account?">
        <Field label="Enter your password to confirm" htmlFor="del-pw"><PasswordInput id="del-pw" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></Field>
        <div className="mt-4 flex justify-end gap-2"><Button variant="secondary" onClick={() => setConfirmAccount(false)}>Cancel</Button><Button variant="danger" disabled={!password} onClick={deleteAccount}>Delete account</Button></div>
      </Dialog>
    </div>
  );
}
