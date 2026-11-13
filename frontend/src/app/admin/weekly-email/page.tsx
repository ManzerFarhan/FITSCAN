"use client";
import { Mail, Send } from "lucide-react";
import { useState } from "react";
import { LoadState, PageHeader, useAdminAction, useAdminData, useIsOwner } from "@/components/admin/ui";
import { Badge } from "@/components/ui/badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Spinner } from "@/components/ui/misc";
import type { WeeklySummaryPreview } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

/** Weekly summary email to the owner: status, preview of this week's email, and "send now". */
export default function AdminWeeklyEmailPage() {
  const isOwner = useIsOwner();
  const { data, error, loading, reload } = useAdminData<WeeklySummaryPreview>("/admin/weekly-summary");
  const send = useAdminAction();
  const [sent, setSent] = useState<string | null>(null);

  return (
    <>
      <PageHeader title="Weekly email" description="A short summary of the week, emailed to the owner. Totals only - no client names or results."
        actions={isOwner && data?.configured && (
          <Button size="sm" disabled={send.busy} onClick={async () => {
            const r = await send.run<{ sent_to: number }>("/admin/weekly-summary/send", { method: "POST" });
            if (r) { setSent(`Sent to ${r.sent_to} owner email(s).`); void reload(); }
          }}>{send.busy ? <Spinner /> : <Send className="h-4 w-4" />}Send now</Button>
        )} />
      <LoadState error={error} loading={loading && !data} />
      {send.error && <Alert tone="error" className="mb-4">{send.error}</Alert>}
      {sent && <Alert tone="success" className="mb-4" onClose={() => setSent(null)}>{sent}</Alert>}
      {data && (
        <div className="grid gap-5 xl:grid-cols-3">
          <Card>
            <CardHeader><CardTitle className="text-base">Status</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p className="flex items-center gap-2">
                {data.configured ? <Badge className="border-green-200 bg-green-50 text-green-800">On</Badge>
                  : <Badge className="border-amber-300 bg-amber-50 text-amber-800">Not set up yet</Badge>}
                {data.configured ? `Every ${DAYS[data.weekday] ?? "Monday"} around 9:00 am IST` : "Emails can't be sent until the email service is connected."}
              </p>
              <p><span className="text-slate-500">Sent to:</span> {data.recipients.join(", ") || "-"}</p>
              <p><span className="text-slate-500">Last sent:</span> {data.last_sent ? formatDate(data.last_sent, true) : "never"}</p>
              {!data.configured && (
                <div className="rounded-lg bg-slate-50 p-3 text-slate-700">
                  <p className="font-medium">To switch it on (5 minutes, free):</p>
                  <ol className="ml-4 mt-1 list-decimal space-y-1">
                    <li>Create a free account at resend.com <b>with the owner email</b> ({data.recipients[0] ?? "your email"}).</li>
                    <li>In Resend, create an API key.</li>
                    <li>Add it on Render as <code>RESEND_API_KEY</code> (or send it to your developer to add).</li>
                  </ol>
                  <p className="mt-2 text-xs text-slate-500">Until you verify your own domain in Resend, emails can only go to the email you signed up with - which is exactly the owner.</p>
                </div>
              )}
            </CardContent>
          </Card>
          <Card className="xl:col-span-2">
            <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Mail className="h-4 w-4" />This week&apos;s email ({data.summary.period})</CardTitle></CardHeader>
            <CardContent>
              <iframe title="Weekly summary preview" srcDoc={data.html} sandbox="" className="h-[560px] w-full rounded-lg border border-slate-200 bg-white" />
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}
