import { AlertTriangle, CalendarClock, FolderKanban, Gauge } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { AreaTrend } from "@/components/charts/AreaTrend";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { EmptyState } from "@/components/ui/empty-state";
import { useProjects } from "@/hooks";
import { useTheme } from "@/contexts/ThemeContext";
import { seriesColor, statusTone } from "@/lib/chart";
import { fmt, pct } from "@/lib/utils";

export default function Projects() {
  const { theme } = useTheme();
  const dark = theme === "dark";
  const { data, isLoading } = useProjects();
  const projects = data?.results ?? [];

  const avgCompletion = projects.length ? projects.reduce((s, p) => s + p.completion_pct, 0) / projects.length : 0;
  const atRisk = projects.filter((p) => p.risk_score >= 50).length;
  const predicted = projects.filter((p) => p.delivery.predicted_delivery).length;

  return (
    <div>
      <PageHeader title="Projects" description="HexaStack Solutions delivery tracking, risk, and predictions." />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard icon={FolderKanban} label="Total projects" value={projects.length} loading={isLoading} tone="primary" />
        <StatCard icon={Gauge} label="Avg completion" value={avgCompletion ? `${avgCompletion.toFixed(0)}%` : null} loading={isLoading} tone="success" />
        <StatCard icon={AlertTriangle} label="At risk" value={atRisk} loading={isLoading} tone={atRisk ? "critical" : "primary"} />
        <StatCard icon={CalendarClock} label="Delivery predicted" value={predicted} loading={isLoading} />
      </div>

      {projects.length === 0 ? (
        <div className="mt-4">
          <EmptyState title="No projects yet" description="Create a project from Settings or run the Project Performance agent to seed sample data." />
        </div>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
          {projects.map((project, idx) => {
            const tone = statusTone(project.risk_score);
            const burndownData = project.burndown.map((b) => ({
              label: new Date(b.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
              remaining: b.remaining,
            }));
            return (
              <Card key={project.id} className="p-4">
                <div className="mb-3 flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium">{project.name}</p>
                    <p className="text-xs text-muted">{project.client || "Internal"}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={project.status === "active" ? "success" : project.status === "completed" ? "primary" : "warning"}>
                      {project.status}
                    </Badge>
                    <Badge variant={tone === "good" ? "success" : tone === "critical" ? "critical" : tone === "serious" ? "warning" : "default"}>
                      risk {project.risk_score}
                    </Badge>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="mb-1 flex justify-between text-xs text-muted">
                    <span>Completion</span>
                    <span className="tabular-nums">{pct(project.completion_pct)}</span>
                  </div>
                  <Progress value={project.completion_pct} tone="gradient" />
                  <div className="mt-2 grid grid-cols-4 gap-2 text-center text-[11px] text-muted">
                    <div>
                      <p className="font-medium text-foreground">Backend</p>
                      {project.backend_pct}%
                    </div>
                    <div>
                      <p className="font-medium text-foreground">Frontend</p>
                      {project.frontend_pct}%
                    </div>
                    <div>
                      <p className="font-medium text-foreground">Testing</p>
                      {project.testing_pct}%
                    </div>
                    <div>
                      <p className="font-medium text-foreground">Deploy</p>
                      {project.deployment_pct}%
                    </div>
                  </div>
                </div>

                <div className="mb-1 flex items-center justify-between text-xs text-muted">
                  <span>Burndown (% remaining)</span>
                  <span className="tabular-nums">
                    velocity {project.velocity}%/wk · {project.pending_bugs} bugs open
                  </span>
                </div>
                {burndownData.length >= 2 ? (
                  <AreaTrend
                    data={burndownData}
                    xKey="label"
                    series={[{ key: "remaining", label: "Remaining %", color: seriesColor(idx % 2, dark) }]}
                    height={150}
                  />
                ) : (
                  <p className="py-6 text-center text-xs text-muted">Not enough snapshots for a burndown yet.</p>
                )}

                {project.delivery.predicted_delivery && (
                  <p className="mt-2 text-xs text-muted">
                    <CalendarClock className="mr-1 inline h-3 w-3" />
                    Estimated delivery <span className="font-medium text-foreground">{project.delivery.predicted_delivery}</span>
                    {project.delivery.confidence ? ` · ${fmt(project.delivery.confidence)}% confidence` : ""}
                  </p>
                )}
              </Card>
            );
          })}
        </div>
      )}

    </div>
  );
}
