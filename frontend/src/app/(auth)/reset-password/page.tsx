"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, PasswordInput } from "@/components/ui/form";
import { Alert } from "@/components/ui/misc";
import { api, ApiError } from "@/lib/api";

function ResetInner() {
  const params = useSearchParams();
  const router = useRouter();
  const [token, setToken] = useState(params.get("token") ?? "");
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [msg, setMsg] = useState<{ tone: "success" | "error" | "info"; text: string } | null>(null);

  const request = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const r = await api<{ message: string; dev_reset_token?: string }>("/auth/reset-password", { method: "POST", json: { email } });
      setMsg({ tone: "info", text: r.message });
      if (r.dev_reset_token) setToken(r.dev_reset_token); // development only: no email service in the prototype
    } catch (err) { setMsg({ tone: "error", text: err instanceof ApiError ? err.message : "Request failed." }); }
  };
  const confirm = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api("/auth/reset-password/confirm", { method: "POST", json: { token, new_password: pw } });
      router.push("/login?reset=1");
    } catch (err) { setMsg({ tone: "error", text: err instanceof ApiError ? err.message : "Reset failed." }); }
  };

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader><div><CardTitle>Reset your password</CardTitle><CardDescription>We'll send a reset link to your email.</CardDescription></div></CardHeader>
      <CardContent className="space-y-6">
        {msg && <Alert tone={msg.tone}>{msg.text}</Alert>}
        {!token ? (
          <form onSubmit={request} className="space-y-4">
            <Field label="Email" htmlFor="rp-email"><Input id="rp-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
            <Button type="submit" className="w-full">Send reset link</Button>
          </form>
        ) : (
          <form onSubmit={confirm} className="space-y-4">
            <p className="text-xs text-slate-500">Development mode: the reset token was filled in automatically because no email service is configured.</p>
            <Field label="New password" htmlFor="rp-pw" hint="At least 8 characters."><PasswordInput id="rp-pw" minLength={8} required value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="new-password" /></Field>
            <Button type="submit" className="w-full">Set new password</Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return <Suspense><ResetInner /></Suspense>;
}
