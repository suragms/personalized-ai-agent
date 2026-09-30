import {
  CheckCircle,
  AlertCircle,
  Clock,
  Wifi,
  WifiOff,
  RefreshCw,
  Database,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useDataSources, useIntegrations } from "@/hooks/useIntelligence";
import type { DataSource, IntegrationConnection } from "@/services/intelligence";
import { normalizeStatus } from "@/lib/status";
import { cn } from "@/lib/utils";

type HealthStatus =
  | "healthy"
  | "needs_attention"
  | "stale"
  | "not_connected"
  | "error"
  | "no_data"
  | "unavailable";

const ERROR_STATES = new Set(["api_error", "unknown_error"]);
const ATTENTION_STATES = new Set([
  "authentication_failed",
  "invalid_credentials",
  "permission_denied",
  "rate_limited",
  "timeout",
  "network_error",
  "service_unavailable",
]);
const DISCONNECTED_STATES = new Set(["disconnected", "not_configured"]);

function getSourceHealth(source: DataSource): HealthStatus {
  const state = normalizeStatus(source.state);
  if (ERROR_STATES.has(state)) return "error";
  if (DISCONNECTED_STATES.has(state)) return "not_connected";
  if (state === "stale") return "stale";
  if (state === "no_data") return "no_data";
  if (state === "connecting" || state === "connected") {
    if (!source.last_synced_at) return "no_data";
    const ageHours =
      (Date.now() - new Date(source.last_synced_at).getTime()) / 3_600_000;
    if (ageHours > source.sync_frequency_hours * 2) return "stale";
    return "healthy";
  }
  if (ATTENTION_STATES.has(state)) return "needs_attention";
  return "unavailable";
}

function getIntegrationHealth(conn: IntegrationConnection): HealthStatus {
  const status = normalizeStatus(conn.status);
  if (ERROR_STATES.has(status)) return "error";
  if (ATTENTION_STATES.has(status)) return "needs_attention";
  if (DISCONNECTED_STATES.has(status)) return "not_connected";
  if (status === "connecting") return "no_data";
  if (status === "connected") {
    if (!conn.last_synced_at) return "no_data";
    return "healthy";
  }
  return "unavailable";
}

const STATUS_LABELS: Record<HealthStatus, string> = {
  healthy: "Healthy",
  needs_attention: "Needs Attention",
  stale: "Stale",
  not_connected: "Not Connected",
  error: "Error",
  no_data: "No Data",
  unavailable: "Unavailable",
};

const STATUS_VARIANT: Record<
  HealthStatus,
  "success" | "warning" | "critical" | "default" | "info"
> = {
  healthy: "success",
  needs_attention: "warning",
  stale: "warning",
  not_connected: "default",
  error: "critical",
  no_data: "info",
  unavailable: "default",
};

const STATUS_ICON: Record<HealthStatus, React.ReactNode> = {
  healthy: <CheckCircle className="h-4 w-4 text-green-500" />,
  needs_attention: <AlertCircle className="h-4 w-4 text-amber-500" />,
  stale: <Clock className="h-4 w-4 text-amber-500" />,
  not_connected: <WifiOff className="h-4 w-4 text-muted" />,
  error: <AlertCircle className="h-4 w-4 text-red-500" />,
  no_data: <Database className="h-4 w-4 text-muted" />,
  unavailable: <Wifi className="h-4 w-4 text-muted" />,
};

function formatAge(isoDate: string | null): string {
  if (!isoDate) return "Never";
  const ms = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(ms / 60_000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function DataHealth({ compact = false }: { compact?: boolean }) {
  const { data: sourcesData, isLoading: sourcesLoading } = useDataSources();
  const { data: integrationsData, isLoading: intLoading } = useIntegrations();

  const loading = sourcesLoading || intLoading;
  const sources = sourcesData?.results ?? [];
  const integrations = integrationsData?.results ?? [];

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5 text-sm">
            <Database className="h-4 w-4" /> Data Health
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (sources.length === 0 && integrations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5 text-sm">
            <Database className="h-4 w-4" /> Data Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted">
            No data sources connected yet. Connect a source to see health status.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5 text-sm">
          <Database className="h-4 w-4" /> Data Health
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {integrations.map((conn) => {
          const health = getIntegrationHealth(conn);
          return (
            <HealthRow
              key={conn.id}
              name={conn.platform}
              type="Integration"
              health={health}
              detail={
                conn.connected_account
                  ? `Connected as ${conn.connected_account}`
                  : STATUS_LABELS[health]
              }
              lastSync={conn.last_synced_at}
              error={conn.last_error}
              compact={compact}
            />
          );
        })}

        {sources.map((source) => {
          const health = getSourceHealth(source);
          return (
            <HealthRow
              key={source.id}
              name={source.name || source.source_type}
              type={source.source_type}
              health={health}
              detail={STATUS_LABELS[health]}
              lastSync={source.last_synced_at}
              error={source.last_error}
              compact={compact}
            />
          );
        })}
      </CardContent>
    </Card>
  );
}

function HealthRow({
  name,
  type,
  health,
  lastSync,
  error,
  compact,
}: {
  name: string;
  type: string;
  health: HealthStatus;
  detail: string; // kept in signature for callers
  lastSync: string | null;
  error: string;
  compact: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-2 rounded-lg border border-border p-3",
        health === "error" && "border-red-500/30 bg-red-500/5",
        health === "healthy" && "border-green-500/20 bg-green-500/5"
      )}
    >
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {STATUS_ICON[health]}
        <div className="min-w-0">
          <p className="truncate text-sm font-medium capitalize">{name}</p>
          {!compact && (
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-[11px] text-muted capitalize">{type}</p>
              {lastSync && (
                <p className="text-[11px] text-muted flex items-center gap-1">
                  <RefreshCw className="h-2.5 w-2.5" />
                  {formatAge(lastSync)}
                </p>
              )}
              {!lastSync && health !== "not_connected" && (
                <p className="text-[11px] text-muted">Never synced</p>
              )}
            </div>
          )}
          {error && (
            <p className="truncate text-[11px] text-red-500">{error}</p>
          )}
        </div>
      </div>
      <div className="flex-shrink-0">
        <Badge variant={STATUS_VARIANT[health]}>{STATUS_LABELS[health]}</Badge>
      </div>
    </div>
  );
}
