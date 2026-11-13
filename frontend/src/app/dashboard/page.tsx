"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { BmiCard } from "@/components/dashboard/BmiCard";
import { DashboardCharts } from "@/components/dashboard/DashboardCharts";
import { FirstReportPanel } from "@/components/dashboard/FirstReportPanel";
import { HealthScoreCard } from "@/components/dashboard/HealthScoreCard";
import { ImportantFindings } from "@/components/dashboard/ImportantFindings";
import { LatestReportCard } from "@/components/dashboard/LatestReportCard";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { Alert, Skeleton } from "@/components/ui/misc";
import { api } from "@/lib/api";
import type { DashboardData } from "@/lib/types";
import demo from "@/mocks/dashboard.json";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    api<DashboardData>("/dashboard")
      .then(setData)
      .catch(() => { setData(demo as DashboardData); setDemoMode(true); });  // FR-DASH-10 offline demo fallback
  }, []);

  const name = data?.user.full_name?.split(" ")[0];
  // No reports yet: one clear "upload your first report" panel instead of empty cards and charts.
  const isNew = !!data && !demoMode && data.cards.total_reports === 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-slate-900">{name ? `Welcome back, ${name}` : "Welcome to FITSCAN"}</h1>
        <p className="text-slate-600">Your lab reports, explained in plain language.</p>
      </div>
      {demoMode && (
        <Alert tone="warning" title="Showing demo data">
          The FITSCAN server could not be reached, so sample data is shown. Start the backend to see your own documents.
        </Alert>
      )}
      {data?.user.is_guest && !demoMode && !isNew && (
        <Alert tone="info">
          You're using FITSCAN as a guest - your documents are kept for 24 hours.{" "}
          <Link href="/register" className="font-medium underline">Create a free account</Link> to keep your history.
        </Alert>
      )}
      {!isNew && <QuickActions />}
      {!data ? (
        <div className="grid gap-3 sm:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
      ) : isNew ? (
        <>
          <FirstReportPanel isGuest={data.user.is_guest} />
          {!data.user.is_guest && <div className="grid gap-6 lg:grid-cols-2"><BmiCard /></div>}
        </>
      ) : (
        <>
          <SummaryCards cards={data.cards} />
          <div className="grid gap-6 lg:grid-cols-2">
            <HealthScoreCard data={data.health_score} locked={data.user.is_guest && !demoMode} />
            <BmiCard />
          </div>
          <DashboardCharts charts={data.charts} />
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <ImportantFindings findings={data.important_findings} />
            </div>
            <div className="space-y-6">
              <LatestReportCard report={data.latest_report} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
