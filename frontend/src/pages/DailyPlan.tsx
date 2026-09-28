import { CalendarDays, AlertCircle, Target, CheckSquare, TrendingUp, Database } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useDailyPlan, useInsights, useAlerts } from "@/hooks/useIntelligence";

export default function DailyPlan() {
  const { data: plan, isLoading, isError, error } = useDailyPlan();
  const { data: insightsData } = useInsights({ status: "new" });
  const { data: alertsData } = useAlerts({ status: "active" });

  const activeAlerts = alertsData?.results ?? [];
  const newInsights = insightsData?.results ?? [];

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Daily Plan" description="Today's priorities and recommendations." />
        <div className="grid gap-4 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-4 space-y-2">
                <Skeleton className="h-5 w-1/3" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div>
        <PageHeader title="Daily Plan" description="Today's priorities and recommendations." />
        <div className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/5 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" />
          <div>
            <p className="font-medium text-red-500">Failed to load daily plan</p>
            <p className="mt-1 text-sm text-muted">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const today = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div>
      <PageHeader
        title="Daily Plan"
        description={today}
        action={
          plan ? (
            <Badge variant="success">Plan available</Badge>
          ) : (
            <Badge variant="default">No plan yet</Badge>
          )
        }
      />

      {!plan && (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-border bg-muted/5 px-6 py-12 text-center">
          <CalendarDays className="h-10 w-10 text-muted" />
          <div>
            <p className="font-medium">No daily plan for today</p>
            <p className="mt-1 text-sm text-muted">
              Not enough connected data to generate a reliable daily plan.
            </p>
            <p className="mt-2 text-xs text-muted">
              Connect a data source and run a sync to enable daily planning.
            </p>
          </div>
        </div>
      )}

      {plan && (
        <div className="space-y-4">
          {/* Focus */}
          {plan.recommended_focus && (
            <Card className="border-primary/30 bg-primary/5">
              <CardContent className="p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-primary mb-1">Recommended Focus</p>
                <p className="text-sm">{plan.recommended_focus}</p>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            {/* Priorities */}
            <PlanSection
              title="Priorities"
              icon={<Target className="h-4 w-4" />}
              empty="No priorities generated for today."
            >
              {plan.priorities.length > 0 ? (
                <ol className="space-y-2">
                  {plan.priorities.map((p, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-primary/15 text-[10px] font-bold text-primary">
                        {i + 1}
                      </span>
                      <span className="text-muted">
                        {typeof p === "string" ? p : JSON.stringify(p)}
                      </span>
                    </li>
                  ))}
                </ol>
              ) : null}
            </PlanSection>

            {/* Tasks */}
            <PlanSection
              title="Tasks"
              icon={<CheckSquare className="h-4 w-4" />}
              empty="No tasks in today's plan."
            >
              {plan.tasks.length > 0 ? (
                <ul className="space-y-1.5">
                  {plan.tasks.map((t, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-muted">
                      <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-muted" />
                      {typeof t === "string" ? t : JSON.stringify(t)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </PlanSection>

            {/* Important Alerts */}
            {plan.important_alerts.length > 0 && (
              <PlanSection
                title="Important Alerts"
                icon={<AlertCircle className="h-4 w-4 text-amber-500" />}
                empty=""
              >
                <ul className="space-y-1.5">
                  {plan.important_alerts.map((a, i) => (
                    <li key={i} className="text-sm text-amber-600 dark:text-amber-400">
                      {typeof a === "string" ? a : JSON.stringify(a)}
                    </li>
                  ))}
                </ul>
              </PlanSection>
            )}

            {/* Potential Blockers */}
            {plan.potential_blockers.length > 0 && (
              <PlanSection
                title="Potential Blockers"
                icon={<AlertCircle className="h-4 w-4 text-red-500" />}
                empty=""
              >
                <ul className="space-y-1.5">
                  {plan.potential_blockers.map((b, i) => (
                    <li key={i} className="text-sm text-red-500">
                      {typeof b === "string" ? b : JSON.stringify(b)}
                    </li>
                  ))}
                </ul>
              </PlanSection>
            )}

            {/* Tomorrow's Priorities */}
            {plan.tomorrow_priorities.length > 0 && (
              <PlanSection
                title="Tomorrow's Priorities"
                icon={<CalendarDays className="h-4 w-4" />}
                empty=""
              >
                <ul className="space-y-1.5">
                  {plan.tomorrow_priorities.map((p, i) => (
                    <li key={i} className="text-sm text-muted">
                      {typeof p === "string" ? p : JSON.stringify(p)}
                    </li>
                  ))}
                </ul>
              </PlanSection>
            )}

            {/* Evening insights */}
            {plan.evening_insights && (
              <PlanSection
                title="Evening Insights"
                icon={<TrendingUp className="h-4 w-4" />}
                empty=""
              >
                <p className="text-sm text-muted">{plan.evening_insights}</p>
              </PlanSection>
            )}
          </div>

          {/* Active Alerts & New Insights summary */}
          {(activeAlerts.length > 0 || newInsights.length > 0) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-1.5 text-sm">
                  <Database className="h-4 w-4" /> Data Basis
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted">
                {activeAlerts.length > 0 && (
                  <p>
                    <span className="font-medium text-foreground">{activeAlerts.length}</span> active alert{activeAlerts.length !== 1 ? "s" : ""} contributing to this plan.
                  </p>
                )}
                {newInsights.length > 0 && (
                  <p>
                    <span className="font-medium text-foreground">{newInsights.length}</span> new insight{newInsights.length !== 1 ? "s" : ""} from connected sources.
                  </p>
                )}
                <p className="text-xs">
                  Plan generated: {new Date(plan.created_at).toLocaleString()}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

function PlanSection({
  title,
  icon,
  empty,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  empty: string;
  children?: React.ReactNode;
}) {
  const hasContent = !!children;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5 text-sm">
          {icon} {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {hasContent ? children : (
          <p className="text-sm text-muted">{empty || "No data available."}</p>
        )}
      </CardContent>
    </Card>
  );
}
