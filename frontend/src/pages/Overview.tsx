import { FolderKanban, Github, GraduationCap, Linkedin, ListTodo, Timer, TrendingUp } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MarkdownView } from "@/components/MarkdownView";
import { RadialScore } from "@/components/charts/RadialScore";
import { ContributionHeatmap } from "@/components/charts/ContributionHeatmap";
import { useOverview, useGithubContributions, useBriefing, useGithubInsights, useGithubAnalytics } from "@/hooks";
import { useAuth } from "@/contexts/AuthContext";
import { fmt } from "@/lib/utils";
import { github } from "@/services";
import { Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

export default function Overview() {
  const { data: overview, isLoading } = useOverview();
  const { data: contributions } = useGithubContributions();
  const { data: morning } = useBriefing("morning");
  const { data: insights } = useGithubInsights();
  const { data: weekly } = useGithubAnalytics(4);
  const { user } = useAuth();
  const qc = useQueryClient();
  const refresh = useQuery({ queryKey: ["github", "repos"], queryFn: github.repos, enabled: false });

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${user?.username}`}
        description="Your command center for coding, projects, and professional growth."
        action={
          <Button
            variant="outline"
            onClick={() => {
              void refresh.refetch();
              void qc.invalidateQueries({ queryKey: ["github"] });
            }}
          >
            <Github className="h-4 w-4" /> Sync GitHub
          </Button>
        }
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        <StatCard icon={Github} label="Commits this week" value={overview?.commits_week} loading={isLoading} tone="primary" />
        <StatCard icon={TrendingUp} label="Productivity score" value={overview?.productivity_score} loading={isLoading} tone="success" />
        <StatCard icon={ListTodo} label="Tasks pending" value={overview?.tasks_pending} loading={isLoading} tone="warning" />
        <StatCard icon={FolderKanban} label="Projects" value={overview?.projects} sub={`${overview?.projects_at_risk ?? 0} at risk`} loading={isLoading} tone={overview && overview.projects_at_risk > 0 ? "critical" : "primary"} />
        <StatCard icon={Timer} label="Active repos" value={overview?.active_repos} loading={isLoading} tone="primary" />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Productivity + contribution */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-sm">Coding activity</CardTitle>
            <Link to="/github">
              <Button variant="ghost" size="sm">View GitHub →</Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            {contributions && contributions.length ? (
              <ContributionHeatmap data={contributions} />
            ) : (
              <p className="text-xs text-muted">No contribution data yet — seed or sync your repositories.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Productivity score</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-2">
            <RadialScore value={weekly?.productivity_score ?? overview?.productivity_score ?? 0} label="this week" size={160} />
            {weekly?.totals && (
              <p className="text-center text-xs text-muted">
                {fmt(weekly.totals.commits)} commits · {fmt(weekly.totals.additions)} lines added · {fmt(weekly.totals.prs_merged)} PRs merged
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Morning briefing */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-sm">Today's briefing</CardTitle>
            <Link to="/tasks">
              <Button variant="ghost" size="sm">Open tasks →</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {morning?.results?.[0] ? (
              <MarkdownView content={morning.results[0].content} className="max-h-80 overflow-y-auto pr-2" />
            ) : (
              <p className="text-xs text-muted">No briefing yet. Run the Daily Productivity agent from the Tasks page.</p>
            )}
          </CardContent>
        </Card>

        {/* AI insights */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <TrendingUp className="h-4 w-4" /> AI insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {insights && insights.length ? (
              insights.slice(0, 5).map((insight) => (
                <div key={insight.id} className="flex items-start gap-2 rounded-md bg-muted/5 p-2">
                  <Badge
                    variant={insight.severity === "critical" ? "critical" : insight.severity === "warning" ? "warning" : "info"}
                  >
                    {insight.severity}
                  </Badge>
                  <p className="text-xs leading-relaxed text-muted">{insight.text}</p>
                </div>
              ))
            ) : (
              <p className="text-xs text-muted">No insights yet — the GitHub agent will surface recommendations here.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick stats */}
      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard icon={FolderKanban} label="Project completion" value={overview?.project_avg_completion ? `${overview.project_avg_completion}%` : null} loading={isLoading} />
        <StatCard icon={Linkedin} label="LinkedIn score" value={overview?.linkedin_score} loading={isLoading} tone="primary" />
        <StatCard icon={Github} label="Resume ATS" value={overview?.resume_ats} loading={isLoading} tone="success" />
        <StatCard icon={GraduationCap} label="Learning open" value={overview?.learning_open} loading={isLoading} tone="warning" />
      </div>
    </div>
  );
}
