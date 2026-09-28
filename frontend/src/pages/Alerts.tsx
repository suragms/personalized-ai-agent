import { useState } from "react";
import { Bell, AlertCircle, CheckCircle, X, Eye, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAlerts, useMarkAlertRead, useResolveAlert } from "@/hooks/useIntelligence";
import type { Alert } from "@/services/intelligence";
import { cn } from "@/lib/utils";

const SEVERITY_VARIANT: Record<string, "critical" | "warning" | "info" | "success" | "default"> = {
  critical: "critical",
  high: "warning",
  medium: "warning",
  low: "info",
  info: "info",
};

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

export default function Alerts() {
  const [filterStatus, setFilterStatus] = useState<string>("active");
  const [filterSeverity, setFilterSeverity] = useState<string>("");
  const [selected, setSelected] = useState<Alert | null>(null);

  const { data, isLoading, isError, error } = useAlerts({
    status: filterStatus || undefined,
  });

  const markRead = useMarkAlertRead();
  const resolve = useResolveAlert();

  const alerts = data?.results ?? [];

  const filtered = filterSeverity
    ? alerts.filter((a) => a.severity === filterSeverity)
    : alerts;

  const sorted = [...filtered].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 5) - (SEVERITY_ORDER[b.severity] ?? 5)
  );

  return (
    <div>
      <PageHeader
        title="Alerts"
        description="Active alerts from your connected data sources."
        action={
          sorted.filter((a) => a.status === "active").length > 0 ? (
            <Badge variant="critical">
              {sorted.filter((a) => a.status === "active").length} active
            </Badge>
          ) : undefined
        }
      />

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="flex gap-1">
          {["active", "read", "resolved", "all"].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStatus(s === "all" ? "" : s)}
              className={cn(
                "rounded-full border px-3 py-0.5 text-xs font-medium capitalize transition-colors",
                (s === "all" ? !filterStatus : filterStatus === s)
                  ? "border-primary/60 bg-primary/10 text-primary"
                  : "border-border text-muted hover:border-primary/30"
              )}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="h-4 w-px bg-border" />

        <div className="flex gap-1">
          {["critical", "high", "medium", "low", "info"].map((sv) => (
            <button
              key={sv}
              onClick={() => setFilterSeverity(sv === filterSeverity ? "" : sv)}
              className={cn(
                "rounded-full border px-3 py-0.5 text-xs font-medium capitalize transition-colors",
                filterSeverity === sv
                  ? "border-primary/60 bg-primary/10 text-primary"
                  : "border-border text-muted hover:border-primary/30"
              )}
            >
              {sv}
            </button>
          ))}
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-4 space-y-2">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-3 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/5 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" />
          <div>
            <p className="font-medium text-red-500">Failed to load alerts</p>
            <p className="mt-1 text-sm text-muted">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && sorted.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-border bg-muted/5 px-6 py-12 text-center">
          <Bell className="h-10 w-10 text-muted" />
          <div>
            <p className="font-medium">No alerts</p>
            <p className="mt-1 text-sm text-muted">
              {filterStatus || filterSeverity
                ? "No alerts match the current filters."
                : "No active alerts. Keep up the good work!"}
            </p>
          </div>
          {(filterStatus || filterSeverity) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setFilterStatus("");
                setFilterSeverity("");
              }}
            >
              Clear filters
            </Button>
          )}
        </div>
      )}

      {/* List */}
      {!isLoading && !isError && sorted.length > 0 && (
        <div className="space-y-3">
          {sorted.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onSelect={() => setSelected(alert)}
              onMarkRead={() => markRead.mutate(alert.id)}
              onResolve={() => resolve.mutate(alert.id)}
              isPending={markRead.isPending || resolve.isPending}
            />
          ))}
        </div>
      )}

      {/* Detail */}
      {selected && (
        <AlertDetail alert={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}

function AlertCard({
  alert,
  onSelect,
  onMarkRead,
  onResolve,
  isPending,
}: {
  alert: Alert;
  onSelect: () => void;
  onMarkRead: () => void;
  onResolve: () => void;
  isPending: boolean;
}) {
  return (
    <Card
      className={cn(
        "cursor-pointer transition-shadow hover:shadow-md",
        alert.status !== "active" && "opacity-70"
      )}
      onClick={onSelect}
    >
      <CardHeader className="pb-2 flex-row items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-1.5 mb-1">
            <Badge variant={SEVERITY_VARIANT[alert.severity] ?? "default"}>
              {alert.severity}
            </Badge>
            {alert.category && (
              <Badge variant="default" className="capitalize">
                {alert.category}
              </Badge>
            )}
            <Badge variant={alert.status === "active" ? "warning" : "success"}>
              {alert.status}
            </Badge>
          </div>
          <CardTitle className="text-sm leading-snug">{alert.title}</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        <p className="text-xs text-muted line-clamp-2">{alert.message}</p>

        <div className="flex items-center justify-between pt-1">
          <p className="text-[10px] text-muted">
            {new Date(alert.created_at).toLocaleDateString()}
            {alert.source_type && ` · ${alert.source_type}`}
          </p>
          <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            {alert.status === "active" && (
              <>
                <button
                  onClick={onMarkRead}
                  disabled={isPending}
                  className="rounded p-1 text-muted hover:text-foreground transition-colors"
                  aria-label="Mark as read"
                >
                  <Eye className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={onResolve}
                  disabled={isPending}
                  className="rounded p-1 text-muted hover:text-green-500 transition-colors"
                  aria-label="Resolve"
                >
                  <CheckCircle className="h-3.5 w-3.5" />
                </button>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AlertDetail({ alert, onClose }: { alert: Alert; onClose: () => void }) {
  const markRead = useMarkAlertRead();
  const resolve = useResolveAlert();

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl rounded-xl border border-border bg-background shadow-xl overflow-y-auto max-h-[90vh]">
        <div className="flex items-start justify-between gap-3 p-5 border-b border-border">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap gap-1.5 mb-2">
              <Badge variant={SEVERITY_VARIANT[alert.severity] ?? "default"}>{alert.severity}</Badge>
              <Badge variant={alert.status === "active" ? "warning" : "success"}>{alert.status}</Badge>
            </div>
            <h2 className="text-base font-semibold">{alert.title}</h2>
          </div>
          <button onClick={onClose} className="text-muted hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 p-5">
          <Section title="Message">
            <p className="text-sm text-muted">{alert.message}</p>
          </Section>

          {alert.evidence && (
            <Section title="Evidence">
              <pre className="rounded bg-muted/10 p-3 text-xs text-muted whitespace-pre-wrap font-mono">
                {alert.evidence}
              </pre>
            </Section>
          )}

          <div className="flex flex-wrap gap-3 text-xs text-muted">
            <span>Source: <strong>{alert.source_type || "—"}</strong></span>
            <span>Category: <strong>{alert.category || "—"}</strong></span>
            <span>Created: <strong>{new Date(alert.created_at).toLocaleString()}</strong></span>
            {alert.read_at && (
              <span>Read: <strong>{new Date(alert.read_at).toLocaleString()}</strong></span>
            )}
            {alert.resolved_at && (
              <span>Resolved: <strong>{new Date(alert.resolved_at).toLocaleString()}</strong></span>
            )}
          </div>

          {alert.status === "active" && (
            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => { markRead.mutate(alert.id); onClose(); }}
                disabled={markRead.isPending}
              >
                {markRead.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
                Mark Read
              </Button>
              <Button
                variant="gradient"
                size="sm"
                onClick={() => { resolve.mutate(alert.id); onClose(); }}
                disabled={resolve.isPending}
              >
                {resolve.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                Resolve
              </Button>
            </div>
          )}
          {alert.status !== "active" && (
            <div className="flex justify-end pt-2">
              <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{title}</p>
      {children}
    </div>
  );
}
