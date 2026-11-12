import { GitCompare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/misc";

export function ComparisonSelector({ count, busy, onCompare, onCancel }: { count: number; busy: boolean; onCompare: () => void; onCancel: () => void }) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-brand-200 bg-brand-50 p-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-brand-900">
        <strong>Compare reports:</strong> tick two or more verified lab reports. Only verified values with matching units are compared.
      </p>
      <div className="flex gap-2">
        <Button variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
        <Button size="sm" disabled={count < 2 || busy} onClick={onCompare}>{busy ? <Spinner /> : <GitCompare className="h-4 w-4" />}Compare {count || ""}</Button>
      </div>
    </div>
  );
}
