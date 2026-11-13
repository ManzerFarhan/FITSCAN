"use client";
import { CheckCircle2 } from "lucide-react";
import { LoadState, PageHeader, useAdminData } from "@/components/admin/ui";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AdminSystem } from "@/lib/types";

/** What the server is running with - useful when something misbehaves. Secrets are never shown. */
export default function AdminSystemPage() {
  const { data, error, loading } = useAdminData<AdminSystem>("/admin/system");
  const groups: [string, [string, string | number][]][] = data ? [
    ["Server", [["Version", data.version], ["Environment", data.environment], ["Database", data.database], ["File storage", data.storage]]],
    ["Report reading", [["OCR engine", data.ocr_engine], ["Tests in dictionary", data.tests_in_dictionary], ["Max upload", `${data.max_upload_mb} MB`]]],
    ["Services", [["Chatbot", data.chatbot], ["Report explanations", data.explanations], ["Centre search", data.centre_search],
      ["Guest data kept for", `${data.guest_retention_hours} hours`]]],
  ] : [];
  return (
    <>
      <PageHeader title="System" description="How the FITSCAN server is configured right now. Keys and passwords are never shown here." />
      <LoadState error={error} loading={loading && !data} />
      {data && (
        <>
          <p className="mb-4 flex items-center gap-2 text-sm text-green-800"><CheckCircle2 className="h-4 w-4" />Server and database are responding.</p>
          <div className="grid gap-5 lg:grid-cols-3">
            {groups.map(([title, rows]) => (
              <Card key={title}>
                <CardHeader><CardTitle className="text-base">{title}</CardTitle></CardHeader>
                <CardContent>
                  <dl className="space-y-2 text-sm">
                    {rows.map(([k, v]) => <div key={k} className="flex justify-between gap-3"><dt className="text-slate-500">{k}</dt><dd className="font-medium text-slate-900">{v}</dd></div>)}
                  </dl>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </>
  );
}
