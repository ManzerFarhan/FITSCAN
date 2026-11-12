"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, PasswordInput } from "@/components/ui/form";
import { Alert, Spinner } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";
import { DISCLAIMER_TEXT } from "@/lib/constants";

function RegisterInner() {
  const { register } = useAuth();
  const router = useRouter();
  const next = useSearchParams().get("next");
  const [f, setF] = useState({ full_name: "", email: "", password: "", confirm: "" });
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (f.password !== f.confirm) return setError("Passwords don't match.");
    setBusy(true); setError(null);
    try {
      await register(f.email, f.password, f.full_name || undefined);
      router.push(next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard");
    } catch (err) {
      const msg = err instanceof ApiError && err.code === "VALIDATION_ERROR" ? "Please enter a valid email and a password of at least 8 characters." : err instanceof Error ? err.message : "Registration failed.";
      setError(msg);
    } finally { setBusy(false); }
  };

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader><div><CardTitle>Create your FITSCAN account</CardTitle><CardDescription>Keep your reports and track changes over time.</CardDescription></div></CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-4">
          <Field label="Full name" htmlFor="r-name"><Input id="r-name" value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} autoComplete="name" /></Field>
          <Field label="Email" htmlFor="r-email"><Input id="r-email" type="email" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} autoComplete="email" /></Field>
          <Field label="Password" htmlFor="r-pw" hint="At least 8 characters."><PasswordInput id="r-pw" required minLength={8} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} autoComplete="new-password" /></Field>
          <Field label="Confirm password" htmlFor="r-pw2"><PasswordInput id="r-pw2" required value={f.confirm} onChange={(e) => setF({ ...f, confirm: e.target.value })} autoComplete="new-password" /></Field>
          <label className="flex items-start gap-2 text-xs text-slate-600">
            <input type="checkbox" className="mt-0.5 h-4 w-4 accent-brand-700" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
            <span>
              I agree to the <Link href="/terms" target="_blank" className="font-medium text-brand-700 underline">Terms &amp; Conditions</Link> and{" "}
              <Link href="/privacy" target="_blank" className="font-medium text-brand-700 underline">Privacy Policy</Link>, and I understand: {DISCLAIMER_TEXT}
            </span>
          </label>
          {error && <Alert tone="error">{error}</Alert>}
          <Button type="submit" className="w-full" disabled={busy || !agree}>{busy && <Spinner />}Create account</Button>
        </form>
        <p className="mt-4 text-center text-sm">Already registered? <Link href={next ? `/login?next=${encodeURIComponent(next)}` : "/login"} className="text-brand-700 hover:underline">Log in</Link></p>
      </CardContent>
    </Card>
  );
}

export default function RegisterPage() {
  return <Suspense><RegisterInner /></Suspense>;
}
