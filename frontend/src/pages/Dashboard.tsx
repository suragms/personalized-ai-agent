import { BrainCircuit, Github, TrendingUp, Bell, CalendarDays, AlertCircle, RefreshCw, Loader2, Activity } from "lucide-react";
import { Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DataHealth } from "@/components/DataHealth";
import {
  useProfile,
  useGitHubStatus,
  useInsights,
  useAlerts,
  useDailyPlan,
  useGitHubSync,
} from "@/hooks/useIntelligence";
import { useSystemHealth } from "@/hooks";
import { useAuth } from "@/contexts/AuthContext";
import type { Insight, Alert } from "@/services/intelligence";
import { statusLabel, statusTone } from "@/lib/status";
import { cn } from "@/lib/utils";

const SEVERITY_VARIANT: Record<string, "critical" | "warning" | "info" | "success" | "default"> = {
  critical: "critical",
  high: "warning",
  medium: "warning",
  low: "info",
  info: "info",
};

export default function Dashboard() {
  const { user } = useAuth();
  const qc = useQueryClient();

  const { data: profile, isLoading: profileLoading } = useProfile();
  const { data: githubStatus, isLoading: githubLoading } = useGitHubStatus();
  const { data: insightsData, isLoading: insightsLoading } = useInsights({ status: "new" });
  const { data: alertsData, isLoading: alertsLoading } = useAlerts({ status: "active" });
  const { data: dailyPlan, isLoading: planLoading } = useDailyPlan();
  const syncMutation = useGitHubSync();

  const insights = insightsData?.results ?? [];
  const alerts = alertsData?.results ?? [];
  const displayName = profile?.professional_title
    ? `${user?.username} — ${profile.professional_title}`
    : user?.username;

  function handleSyncAll() {
    if (githubStatus?.connected) {
      syncMutation.mutate(undefined, {
        onSuccess: () => {
          qc.invalidateQueries({ queryKey: ["intelligence"] });
        },
      });
    }
  }

  return (
    <div>
      <PageHeader
        title="Personalized AI Agent"
        description={displayName ?? "Your intelligence command centre."}
        action={
          <Button
            variant="outline"
            size="sm"
            onClick={handleSyncAll}
            disabled={syncMutation.isPending || !githubStatus?.connected}
            title={!githubStatus?.connected ? "Connect GitHub first" : undefined}
          >
            {syncMutation.isPending ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Syncing...</>
            ) : (
              <><RefreshCw className="h-4 w-4" /> Sync</>
            )}
          </Button>
        }
      />

      {/* Onboarding prompt if not completed */}
      {!profileLoading && profile && !profile.onboarding_completed && (
        <div className="mb-4 flex items-start justify-between gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4">
          <div className="flex items-start gap-3">
            <BrainCircuit className="mt-0.5 h-5 w-5 text-primary" />
            <div>
              <p className="font-medium text-primary">Finish setting up your agent</p>
              <p className="mt-0.5 text-sm text-muted">
                Complete onboarding to connect your data sources and enable personalised insights.
              </p>
            </div>
          </div>
          <Link to="/onboarding">
            <Button variant="gradient" size="sm">Continue Setup</Button>
          </Link>
        </div>
      )}

      {/* Top section: GitHub + Alerts summary */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* GitHub Status */}
        <Card className={cn(
          "lg:col-span-1",
          githubStatus?.connected ? "border-green-500/20" : "border-border"
        )}>
          <CardHeader className="flex-row items-center justify-between pb-2">
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <Github className="h-4 w-4" /> GitHub
            </CardTitle>
            <Link to="/integrations/github">
              <Button variant="ghost" size="sm" className="text-xs">Manage →</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {githubLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            ) : githubStatus?.connected ? (
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  <p className="text-sm font-medium text-green-500">Connected</p>
                </div>
                <p className="text-xs text-muted">@{githubStatus.account}</p>
                {githubStatus.last_synced_at ? (
                  <p className="text-xs text-muted">
                    Last sync: {new Date(githubStatus.last_synced_at).toLocaleString()}
                  </p>
                ) : (
                  <p className="text-xs text-amber-500">Connected but not yet synced</p>
                )}
                {githubStatus.last_error && (
                  <p className="text-xs text-red-500 truncate">{githubStatus.last_error}</p>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-muted">No GitHub data available.</p>
                <Link to="/integrations/github">
                  <Button variant="outline" size="sm" className="w-full">
                    <Github className="h-4 w-4" /> Connect GitHub
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Active Alerts */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex-row items-center justify-between pb-2">
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <Bell className="h-4 w-4" /> Alerts
              {alerts.length > 0 && (
                <Badge variant="critical">{alerts.length}</Badge>
              )}
            </CardTitle>
            <Link to="/alerts">
              <Button variant="ghost" size="sm" className="text-xs">View all →</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {alertsLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            ) : alerts.length === 0 ? (
              <p className="text-sm text-muted">No active alerts.</p>
            ) : (
              <ul className="space-y-2">
                {alerts.slice(0, 3).map((alert) => (
                  <AlertRow key={alert.id} alert={alert} />
                ))}
                {alerts.length > 3 && (
                  <li className="text-xs text-muted pt-1">
                    +{alerts.length - 3} more alert{alerts.length - 3 !== 1 ? "s" : ""}
                  </li>
                )}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Daily Plan summary */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex-row items-center justify-between pb-2">
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <CalendarDays className="h-4 w-4" /> Today
            </CardTitle>
            <Link to="/daily-plan">
              <Button variant="ghost" size="sm" className="text-xs">Full plan →</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {planLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            ) : dailyPlan?.recommended_focus ? (
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-primary">Focus</p>
                <p className="text-sm text-muted">{dailyPlan.recommended_focus}</p>
                {dailyPlan.priorities.length > 0 && (
                  <p className="text-xs text-muted">
                    {dailyPlan.priorities.length} priorit{dailyPlan.priorities.length === 1 ? "y" : "ies"}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted">
                {dailyPlan
                  ? "No focus set for today."
                  : "Not enough connected data to generate a daily plan."}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Insights */}
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex-row items-center justify-between pb-2">
              <CardTitle className="flex items-center gap-1.5 text-sm">
                <TrendingUp className="h-4 w-4" /> Insights
                {insights.length > 0 && (
                  <Badge variant="info">{insights.length} new</Badge>
                )}
              </CardTitle>
              <Link to="/insights">
                <Button variant="ghost" size="sm" className="text-xs">View all →</Button>
              </Link>
            </CardHeader>
            <CardContent>
              {insightsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="space-y-1">
                      <Skeleton className="h-4 w-1/2" />
                      <Skeleton className="h-3 w-full" />
                    </div>
                  ))}
                </div>
              ) : insights.length === 0 ? (
                <div className="text-center py-4 space-y-2">
                  <TrendingUp className="mx-auto h-8 w-8 text-muted" />
                  <p className="text-sm text-muted">
                    No new insights.{" "}
                    {!githubStatus?.connected && (
                      <>
                        <Link to="/integrations/github" className="text-primary underline">
                          Connect GitHub
                        </Link>{" "}
                        to generate insights.
                      </>
                    )}
                    {githubStatus?.connected && !githubStatus?.last_synced_at && (
                      <>Run a sync to generate insights.</>
                    )}
                  </p>
                </div>
              ) : (
                <ul className="space-y-3">
                  {insights.slice(0, 5).map((insight) => (
                    <InsightRow key={insight.id} insight={insight} />
                  ))}
                  {insights.length > 5 && (
                    <li className="text-xs text-muted pt-1">
                      +{insights.length - 5} more insight{insights.length - 5 !== 1 ? "s" : ""}
                    </li>
                  )}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Data Health */}
        <div className="lg:col-span-1">
          <DataHealth compact />
        </div>
      </div>

      {/* System health — live service probes from GET /api/health/ */}
      <SystemHealthCard />

      {/* Sync error */}
      {syncMutation.isError && (
        <div className="mt-4 flex items-start gap-2 rounded-xl border border-red-500/30 bg-red-500/5 p-3 text-sm text-red-500">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          Sync failed: {syncMutation.error instanceof Error ? syncMutation.error.message : "Unknown error"}
        </div>
      )}
    </div>
  );
}

function AlertRow({ alert }: { alert: Alert }) {
  return (
    <li className="flex items-start gap-2">
      <Badge variant={SEVERITY_VARIANT[alert.severity] ?? "default"} className="mt-0.5 flex-shrink-0">
        {alert.severity}
      </Badge>
      <p className="text-xs text-muted line-clamp-2">{alert.title}</p>
    </li>
  );
}

function InsightRow({ insight }: { insight: Insight }) {
  return (
    <li className="space-y-0.5 border-l-2 pl-3"
      style={{
        borderColor:
          insight.severity === "critical"
            ? "#d03b3b"
            : insight.severity === "high"
            ? "#f59e0b"
            : "#6366f1",
      }}
    >
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge variant={SEVERITY_VARIANT[insight.severity] ?? "default"}>{insight.severity}</Badge>
        <p className="text-xs font-medium">{insight.title}</p>
      </div>
      {insight.description && (
        <p className="text-xs text-muted line-clamp-1">{insight.description}</p>
      )}
      {insight.recommended_action && (
        <p className="text-[11px] text-primary">{insight.recommended_action}</p>
      )}
    </li>
  );
}

function SystemHealthCard() {
  const { data: health, isLoading, isError } = useSystemHealth();

  if (isLoading) {
    return (
      <Card className="mt-4">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-1.5 text-sm">
            <Activity className="h-4 w-4" /> System Health
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
      </Card>
    );
  }

  if (isError || !health) return null;

  const overallVariant = health.status === "ok" ? "success" : health.status === "degraded" ? "warning" : "critical";
  const services = Object.entries(health.services);

  return (
    <Card className="mt-4">
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-1.5 text-sm">
          <Activity className="h-4 w-4" /> System Health
        </CardTitle>
        <Badge variant={overallVariant}>{health.status}</Badge>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {services.map(([name, check]) => (
            <Badge key={name} variant={statusTone(check.status)} title={check.detail ?? undefined}>
              {name}: {statusLabel(check.status)}
            </Badge>
          ))}
        </div>
        <p className="mt-2 text-[11px] text-muted">Live service checks � refreshed every minute.</p>
      </CardContent>
    </Card>
  );
}
