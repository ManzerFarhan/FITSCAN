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

function LoginInner() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      await login(email, password);
      const next = params.get("next");
      router.push(next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed.");
    } finally { setBusy(false); }
  };

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader><div><CardTitle>Log in to FITSCAN</CardTitle><CardDescription>Documents you uploaded as a guest will be moved into your account.</CardDescription></div></CardHeader>
      <CardContent>
        {params.get("changed") && <Alert tone="success" className="mb-4">Password changed. Please log in again.</Alert>}
        {params.get("reset") && <Alert tone="success" className="mb-4">Password reset. Log in with your new password.</Alert>}
        <form onSubmit={submit} className="space-y-4">
          <Field label="Email" htmlFor="l-email"><Input id="l-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" /></Field>
          <Field label="Password" htmlFor="l-pw"><PasswordInput id="l-pw" required value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></Field>
          {error && <Alert tone="error">{error}</Alert>}
          <Button type="submit" className="w-full" disabled={busy}>{busy && <Spinner />}Log in</Button>
        </form>
        <div className="mt-4 flex justify-between text-sm">
          <Link href="/reset-password" className="text-brand-700 hover:underline">Forgot password?</Link>
          <Link href={params.get("next") ? `/register?next=${encodeURIComponent(params.get("next")!)}` : "/register"} className="text-brand-700 hover:underline">Create account</Link>
        </div>
      </CardContent>
    </Card>
  );
}

export default function LoginPage() {
  return <Suspense><LoginInner /></Suspense>;
}
