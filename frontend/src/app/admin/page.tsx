"use client";
import { RefreshCw } from "lucide-react";
import Link from "next/link";
import { DailyBars, LoadState, PageHeader, StatTile, useAdminData } from "@/components/admin/ui";
import { DocStatusBadge } from "@/components/ui/badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DocumentStatus } from "@/lib/constants";
import type { AdminOverview } from "@/lib/types";

/** Admin overview: headline numbers, sign-ups and uploads per day, reading health. */
export default function AdminOverviewPage() {
  const { data, error, loading, reload } = useAdminData<AdminOverview>("/admin/overview?days=30");
  const rate = data?.read_success_rate;

  return (
    <>
      <PageHeader title="Overview" description="How FITSCAN is being used, and how well reports are being read."
        actions={<Button variant="secondary" size="sm" onClick={reload} disabled={loading}><RefreshCw className="h-4 w-4" />Refresh</Button>} />
      <LoadState error={error} loading={loading && !data} />
      {data && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile label="Clients" value={data.users} sub={`+${data.users_7d} new this week`} />
            <StatTile label="Active this week" value={data.active_7d} sub={`${data.suspended} suspended`} />
            <StatTile label="Reports" value={data.documents} sub={`+${data.documents_7d} this week`} />
            <StatTile label="Reading success" value={rate == null ? "-" : `${Math.round(rate * 100)}%`}
              sub={`${data.failed} report${data.failed === 1 ? "" : "s"} could not be read`} tone={data.failed ? "warn" : undefined} />
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle className="text-base">New sign-ups per day</CardTitle></CardHeader>
              <CardContent><DailyBars data={data.signups_daily} label="Sign-ups" /></CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-base">Reports uploaded per day</CardTitle></CardHeader>
              <CardContent><DailyBars data={data.uploads_daily} label="Reports" /></CardContent>
            </Card>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Reports by status</CardTitle>
                <CardDescription>Click a status to see those reports.</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="divide-y divide-slate-100 text-sm">
                  {Object.entries(data.by_status).sort((a, b) => b[1] - a[1]).map(([s, n]) => (
                    <li key={s}>
                      <Link href={`/admin/reports?status=${s}`} className="flex items-center justify-between rounded px-1 py-2 hover:bg-slate-50">
                        <DocStatusBadge status={s as DocumentStatus} /><span className="font-medium tabular-nums">{n}</span>
                      </Link>
                    </li>
                  ))}
                  {!Object.keys(data.by_status).length && <li className="py-2 text-slate-500">No reports yet.</li>}
                </ul>
                <p className="mt-3 text-xs text-slate-500">{data.guests_active} guest session{data.guests_active === 1 ? "" : "s"} active now · {data.parameters} test results read in total</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Test names not recognised</CardTitle>
                <CardDescription>Printed names that matched no test in the dictionary - the best candidates to add next.</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="divide-y divide-slate-100 text-sm">
                  {data.unrecognised_tests.map((t) => (
                    <li key={t.name} className="flex justify-between gap-3 py-2"><span className="truncate">{t.name}</span><span className="tabular-nums text-slate-500">{t.count}x</span></li>
                  ))}
                  {!data.unrecognised_tests.length && <li className="py-2 text-slate-500">None - every test name was recognised.</li>}
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
