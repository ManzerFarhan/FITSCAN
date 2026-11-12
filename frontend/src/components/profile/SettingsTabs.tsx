"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Field, Input, PasswordInput } from "@/components/ui/form";
import { Alert, Tabs } from "@/components/ui/misc";
import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";
import { PrivacyControls } from "./PrivacyControls";
import { ProfileForm } from "./ProfileForm";

type Tab = "account" | "location" | "privacy";

/** FR-PROF-4: account, location, privacy. */
export function SettingsTabs({ user, onSaved }: { user: User; onSaved: (u: User) => void }) {
  const [tab, setTab] = useState<Tab>("account");
  return (
    <div className="space-y-4">
      <Tabs<Tab> value={tab} onChange={setTab} tabs={[
        { value: "account", label: "Account" }, { value: "location", label: "Location" }, { value: "privacy", label: "Privacy" },
      ]} />
      {tab === "account" && <AccountSettings user={user} onSaved={onSaved} />}
      {tab === "location" && <ProfileForm user={user} onSaved={onSaved} fields="location" />}
      {tab === "privacy" && <PrivacyControls user={user} onSaved={onSaved} />}
    </div>
  );
}

function AccountSettings({ user, onSaved }: { user: User; onSaved: (u: User) => void }) {
  const [email, setEmail] = useState(user.email);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [msg, setMsg] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  const changeEmail = async () => {
    try { onSaved(await api<User>("/profile", { method: "PATCH", json: { email, current_password: current } })); setMsg({ tone: "success", text: "Email updated." }); }
    catch (e) { setMsg({ tone: "error", text: e instanceof ApiError ? e.message : "Could not update email." }); }
  };
  const changePassword = async () => {
    try { await api("/profile/password", { method: "POST", json: { current_password: current, new_password: next } }); window.location.href = "/login?changed=1"; }
    catch (e) { setMsg({ tone: "error", text: e instanceof ApiError ? e.message : "Could not change password." }); }
  };

  return (
    <div className="max-w-lg space-y-4">
      {msg && <Alert tone={msg.tone}>{msg.text}</Alert>}
      <Field label="Current password" htmlFor="a-cur" hint="Needed to change your email or password."><PasswordInput id="a-cur" value={current} onChange={(e) => setCurrent(e.target.value)} autoComplete="current-password" /></Field>
      <div className="flex items-end gap-2">
        <div className="flex-1"><Field label="Email" htmlFor="a-email"><Input id="a-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" /></Field></div>
        <Button variant="secondary" disabled={!current || email === user.email} onClick={changeEmail}>Update email</Button>
      </div>
      <div className="flex items-end gap-2">
        <div className="flex-1"><Field label="New password" htmlFor="a-new" hint="At least 8 characters. You'll be signed out everywhere."><PasswordInput id="a-new" value={next} minLength={8} onChange={(e) => setNext(e.target.value)} autoComplete="new-password" /></Field></div>
        <Button variant="secondary" disabled={!current || next.length < 8} onClick={changePassword}>Change password</Button>
      </div>
    </div>
  );
}

