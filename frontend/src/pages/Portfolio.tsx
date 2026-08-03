import { ExternalLink, Globe, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { usePortfolio, useRefreshPortfolio } from "@/hooks";
import { cn } from "@/lib/utils";

export default function Portfolio() {
  const { data } = usePortfolio();
  const refresh = useRefreshPortfolio();
  const projects = data?.results ?? [];

  async function onRefresh() {
    try {
      const updated = await refresh.mutateAsync();
      toast.success(`${updated.length} portfolio projects refreshed from GitHub`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Refresh failed");
    }
  }

  return (
    <div>
      <PageHeader
        title="Portfolio"
        description="Auto-synced from your repositories — a new GitHub release refreshes the matching project."
        action={
          <Button variant="outline" onClick={onRefresh} disabled={refresh.isPending}>
            <RefreshCw className={cn("h-4 w-4", refresh.isPending && "animate-spin")} /> Sync from GitHub
          </Button>
        }
      />

      {projects.length === 0 ? (
        <EmptyState title="No portfolio projects" description="Sync from GitHub to build your portfolio automatically." />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => (
            <Card key={project.id} className="group p-4 transition-transform hover:-translate-y-0.5">
              <div className="mb-2 flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate font-medium">{project.name}</p>
                  {project.repository && <p className="truncate text-xs text-muted">{project.repository}</p>}
                </div>
                <Badge
                  variant={project.deployment_status === "live" ? "success" : project.deployment_status === "staging" ? "warning" : "default"}
                >
                  {project.deployment_status}
                </Badge>
              </div>

              <p className="mb-3 line-clamp-3 min-h-12 text-sm text-muted">{project.description || "No description."}</p>

              <div className="mb-3 flex flex-wrap gap-1.5">
                {project.skills.slice(0, 5).map((skill) => (
                  <Badge key={skill} variant="violet">{skill}</Badge>
                ))}
              </div>

              <div className="flex items-center justify-between text-xs text-muted">
                <span>
                  {project.last_release_tag ? (
                    <>
                      Latest release <code className="font-mono">{project.last_release_tag}</code>
                    </>
                  ) : (
                    "No releases yet"
                  )}
                </span>
                {project.live_url && (
                  <a href={project.live_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-foreground">
                    <ExternalLink className="h-3 w-3" /> Live
                  </a>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <div className="mt-6">
        <Card className="p-4">
          <p className="mb-1 flex items-center gap-1.5 text-sm font-medium">
            <Globe className="h-4 w-4" /> How it works
          </p>
          <p className="text-xs leading-relaxed text-muted">
            The Portfolio agent mirrors your active GitHub repositories. When a release is published
            (or you run the agent), the project card updates its skills, deployment status, and latest
            release tag automatically.
          </p>
        </Card>
      </div>
    </div>
  );
}
