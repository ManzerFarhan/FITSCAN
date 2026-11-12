"use client";
import { FileText, GitCompare } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { HistoricalUpload } from "@/components/profile/HistoricalUpload";
import { ProfileForm } from "@/components/profile/ProfileForm";
import { SettingsTabs } from "@/components/profile/SettingsTabs";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface Records {
  lab_reports: number; analyses: number;
  comparisons: { id: string; created_at: string; documents: number; summary: string | null }[];
}

export default function ProfilePage() {
  const { user, loading, setUser } = useAuth();
  const [records, setRecords] = useState<Records | null>(null);

  useEffect(() => { if (user) api<Records>("/profile/records").then(setRecords).catch(() => undefined); }, [user]);

  if (loading) return <Skeleton className="h-64" />;
  if (!user) {
    return (
      <Card className="mx-auto max-w-lg">
        <CardHeader><div><CardTitle>Your profile</CardTitle><CardDescription>Create a free account to keep your medical history, upload older reports and set your preferences.</CardDescription></div></CardHeader>
        <CardContent className="flex gap-2">
          <Link href="/register" className={buttonVariants()}>Create account</Link>
          <Link href="/login" className={buttonVariants({ variant: "secondary" })}>Log in</Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Profile & Settings</h1>
        <p className="text-slate-600">Member since {formatDate(user.created_at)}</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card><CardHeader><CardTitle>Personal details</CardTitle></CardHeader><CardContent><ProfileForm user={user} onSaved={setUser} /></CardContent></Card>
          <Card><CardHeader><CardTitle>Upload previous documents</CardTitle></CardHeader><CardContent><HistoricalUpload /></CardContent></Card>
          <Card><CardHeader><CardTitle>Settings</CardTitle></CardHeader><CardContent><SettingsTabs user={user} onSaved={setUser} /></CardContent></Card>
        </div>
        <Card className="h-fit">
          <CardHeader><CardTitle>Your records</CardTitle></CardHeader>
          <CardContent>
            {!records ? <Skeleton className="h-40" /> : (
              <div className="space-y-4 text-sm">
                <ul className="space-y-2">
                  <li className="flex items-center gap-2"><FileText className="h-4 w-4 text-brand-700" />{records.lab_reports} lab reports ({records.analyses} analysed)</li>
                  <li className="flex items-center gap-2"><GitCompare className="h-4 w-4 text-sky-700" />{records.comparisons.length} comparisons</li>
                </ul>
                {records.comparisons.length > 0 && (
                  <div><p className="font-medium text-slate-900">Recent comparisons</p>
                    <ul className="mt-1 space-y-1 text-slate-600">{records.comparisons.map((c) => <li key={c.id}>{formatDate(c.created_at)} · {c.documents} reports</li>)}</ul></div>
                )}
                <Link href="/history" className="text-brand-700 hover:underline">Open full history</Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
