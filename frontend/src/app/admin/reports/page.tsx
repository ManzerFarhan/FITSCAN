"use client";
import { Search } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ReportsTable } from "@/components/admin/ReportsTable";
import { LoadState, PageHeader, Pager, useAdminData } from "@/components/admin/ui";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/form";
import { DOCUMENT_STATUSES } from "@/lib/constants";
import type { AdminDocument, Paged } from "@/lib/types";

const SIZE = 25;
const STATUS_LABEL: Record<string, string> = {
  UPLOADED: "Waiting", PREPROCESSING: "Preparing", OCR_RUNNING: "Reading (OCR)", EXTRACTING: "Extracting",
  NEEDS_VERIFICATION: "Needs checking", EXTRACTED: "Extracted", VERIFIED: "Verified", ANALYZED: "Analysed", FAILED: "Failed",
};

function Reports() {
  const initial = useSearchParams().get("status") ?? "";
  const [status, setStatus] = useState(initial);
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const params = new URLSearchParams({ ...(status && { status }), ...(query && { q: query }) });
  const { data, error, loading } = useAdminData<Paged<AdminDocument>>(`/admin/documents?${params}&limit=${SIZE}&offset=${page * SIZE}`);

  return (
    <>
      <PageHeader title="Reports" description="Every uploaded report, newest first. Open one to see what was read, the original file, or to read it again." />
      <Card>
        <CardContent className="space-y-4 p-4">
          <div className="flex flex-wrap gap-2">
            <form className="flex min-w-[260px] flex-1 gap-2" onSubmit={(e) => { e.preventDefault(); setPage(0); setQuery(q.trim()); }}>
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search file name, lab or client email" aria-label="Search reports" />
              <Button type="submit" variant="secondary"><Search className="h-4 w-4" />Search</Button>
            </form>
            <Select aria-label="Status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(0); }} className="w-auto">
              <option value="">All statuses</option>
              {DOCUMENT_STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABEL[s] ?? s}</option>)}
            </Select>
          </div>
          <LoadState error={error} loading={loading && !data} />
          {data && <><ReportsTable docs={data.items} showOwner /><Pager total={data.total} page={page} size={SIZE} onPage={setPage} /></>}
        </CardContent>
      </Card>
    </>
  );
}

export default function AdminReportsPage() {
  return <Suspense><Reports /></Suspense>;
}
