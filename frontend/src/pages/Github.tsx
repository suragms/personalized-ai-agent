import { useMemo } from "react";
import { Github as GithubIcon } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { ChartCard, Legend } from "@/components/charts/ChartCard";
import { AreaTrend } from "@/components/charts/AreaTrend";
import { BarTrend } from "@/components/charts/BarTrend";
import { RadialScore } from "@/components/charts/RadialScore";
import { ContributionHeatmap } from "@/components/charts/ContributionHeatmap";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useGithubAnalytics, useGithubContributions, useGithubInsights, useGithubRepos } from "@/hooks";
import { useTheme } from "@/contexts/ThemeContext";
import { seriesColor } from "@/lib/chart";
import { fmt, relativeTime } from "@/lib/utils";

const statusVariant = (status: string) =>
  status === "active" ? "success" : status === "at_risk" ? "warning" : "critical";

export default function Github() {
  const { theme } = useTheme();
  const dark = theme === "dark";
  const { data: analytics, isLoading } = useGithubAnalytics(8);
  const { data: contributions } = useGithubContributions();
  const { data: repos } = useGithubRepos();
  const { data: insights } = useGithubInsights();

  const daily = useMemo(
    () => analytics?.daily.map((d) => ({ ...d, label: new Date(d.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }) })) ?? [],
    [analytics]
  );
  const weeklyByRepo = useMemo(
    () =>
      analytics?.repos.map((r) => ({
        repo: r.name.split("/").pop() ?? r.name,
        commits: r.commits,
        additions: Math.round(r.additions / 100) / 10,
      })) ?? [],
    [analytics]
  );

  return (
    <div>
      <PageHeader title="GitHub Analytics" description="Repositories, contributions, and coding productivity." />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard icon={GithubIcon} label="Commits (period)" value={analytics?.totals.commits} loading={isLoading} tone="primary" />
        <StatCard icon={GithubIcon} label="Lines added" value={fmt(analytics?.totals.additions)} loading={isLoading} />
        <StatCard icon={GithubIcon} label="PRs merged" value={analytics?.totals.prs_merged} loading={isLoading} tone="success" />
        <StatCard icon={GithubIcon} label="Active repos" value={analytics?.totals.active_repos} loading={isLoading} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard
          title="Daily commits"
          description="Last 8 weeks"
          className="lg:col-span-2"
          legend={<Legend items={[{ label: "Commits", color: seriesColor(0, dark) }]} />}
        >
          <AreaTrend data={daily} xKey="label" series={[{ key: "commits", label: "Commits" }]} height={240} />
        </ChartCard>

        <Card className="p-4">
          <div className="flex flex-col items-center gap-2">
            <p className="text-sm font-medium">Productivity score</p>
            <RadialScore value={analytics?.productivity_score ?? 0} label="score /100" size={170} />
            <p className="text-center text-xs text-muted">
              Based on commit volume, code added, consistency, and pull-through.
            </p>
          </div>
        </Card>
      </div>

      <div className="mt-4">
        <Card className="p-4">
          <p className="mb-2 text-sm font-medium">Contribution heatmap — last 90 days</p>
          {contributions && contributions.length ? (
            <ContributionHeatmap data={contributions} />
          ) : (
            <p className="text-xs text-muted">No contribution data yet.</p>
          )}
        </Card>
      </div>

      <div className="mt-4">
        <Tabs defaultValue="repos">
          <TabsList>
            <TabsTrigger value="repos">Repositories</TabsTrigger>
            <TabsTrigger value="weekly">Weekly trend</TabsTrigger>
            <TabsTrigger value="insights">AI recommendations</TabsTrigger>
          </TabsList>

          <TabsContent value="repos">
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-border text-xs text-muted">
                      <tr>
                        <th className="px-4 py-2 font-medium">Repository</th>
                        <th className="px-4 py-2 font-medium">Language</th>
                        <th className="px-4 py-2 font-medium">Status</th>
                        <th className="px-4 py-2 text-right font-medium">Commits</th>
                        <th className="px-4 py-2 text-right font-medium">Stars</th>
                        <th className="px-4 py-2 text-right font-medium">Last commit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(repos?.results ?? []).map((repo) => (
                        <tr key={repo.id} className="border-b border-border/60 last:border-0 hover:bg-muted/5">
                          <td className="px-4 py-2.5">
                            <a href={repo.url} target="_blank" rel="noreferrer" className="font-medium hover:underline">
                              {repo.full_name}
                            </a>
                            {repo.description && <p className="max-w-md truncate text-xs text-muted">{repo.description}</p>}
                          </td>
                          <td className="px-4 py-2.5 text-xs text-muted">{repo.language || "—"}</td>
                          <td className="px-4 py-2.5">
                            <Badge variant={statusVariant(repo.status)}>{repo.status}</Badge>
                          </td>
                          <td className="px-4 py-2.5 text-right tabular-nums">{fmt(analytics?.repos.find((r) => r.name === repo.full_name)?.commits ?? 0)}</td>
                          <td className="px-4 py-2.5 text-right tabular-nums">{repo.stars}</td>
                          <td className="px-4 py-2.5 text-right text-xs text-muted">{relativeTime(repo.last_commit_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="weekly">
            <ChartCard
              title="Commits by repository (period)"
              legend={<Legend items={weeklyByRepo.slice(0, 4).map((r, i) => ({ label: r.repo, color: seriesColor(i, dark) }))} />}
            >
              <BarTrend data={weeklyByRepo.slice(0, 8)} xKey="repo" series={[{ key: "commits", label: "Commits" }]} height={260} />
            </ChartCard>
          </TabsContent>

          <TabsContent value="insights">
            <div className="space-y-2">
              {insights && insights.length ? (
                insights.map((insight) => (
                  <Card key={insight.id} className="flex items-start gap-3 p-3">
                    <Badge variant={insight.severity === "critical" ? "critical" : insight.severity === "warning" ? "warning" : "info"}>
                      {insight.severity}
                    </Badge>
                    <p className="text-sm text-muted">{insight.text}</p>
                  </Card>
                ))
              ) : (
                <p className="text-sm text-muted">Run the GitHub agent to generate recommendations.</p>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
