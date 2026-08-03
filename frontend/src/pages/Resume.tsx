import { FileDown, FileText, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RadialScore } from "@/components/charts/RadialScore";
import { MarkdownView } from "@/components/MarkdownView";
import { EmptyState } from "@/components/ui/empty-state";
import { useRegenerateResume, useResume } from "@/hooks";
import { apiDownload } from "@/lib/api";
import { resume as resumeService } from "@/services";
import { cn, shortDate } from "@/lib/utils";

export default function Resume() {
  const { data: resume, isLoading } = useResume();
  const regenerate = useRegenerateResume();

  async function onRegenerate() {
    try {
      await regenerate.mutateAsync();
      toast.success("Resume updated from your latest activity");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Regeneration failed");
    }
  }

  if (isLoading) {
    return <div className="space-y-4"><div className="h-8 w-48 animate-pulse rounded bg-muted/20" /><div className="h-96 animate-pulse rounded bg-muted/10" /></div>;
  }

  if (!resume) {
    return (
      <div>
        <PageHeader title="Resume" description="Auto-updated from your GitHub and project activity." />
        <EmptyState
          title="No resume yet"
          description="Generate your first version from current activity."
          action={<Button onClick={onRegenerate}><RefreshCw className="h-4 w-4" /> Generate resume</Button>}
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Resume"
        description={`Version ${resume.version_number} · updated ${shortDate(resume.created_at)}`}
        action={
          <Button onClick={onRegenerate} disabled={regenerate.isPending}>
            <RefreshCw className={cn("h-4 w-4", regenerate.isPending && "animate-spin")} /> Regenerate
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">{resume.full_name} — {resume.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <MarkdownView content={resume.content} className="max-h-[36rem] overflow-y-auto pr-2" />
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardContent className="flex flex-col items-center gap-2 p-4">
              <p className="text-sm font-medium">ATS compatibility</p>
              <RadialScore value={resume.ats_score} label="ATS score" size={150} />
              <p className="text-center text-xs text-muted">
                Keywords matched against common full-stack/AI job descriptions.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3 p-4">
              <p className="text-sm font-medium">Exports</p>
              <div className="flex flex-wrap gap-2">
                {(["pdf", "docx"] as const).map((fmt) => (
                  <Button key={fmt} variant="secondary" size="sm" onClick={() => void apiDownload(resumeService.exportUrl(resume.id, fmt), `resume-v${resume.version_number}.${fmt}`)}>
                    <FileDown className="h-4 w-4" /> {fmt.toUpperCase()}
                  </Button>
                ))}
              </div>

              <p className="pt-2 text-sm font-medium">Skills ({resume.skills.length})</p>
              <div className="flex flex-wrap gap-1.5">
                {resume.skills.map((skill) => (
                  <Badge key={skill} variant="violet">{skill}</Badge>
                ))}
              </div>

              {resume.keywords_missing.length > 0 && (
                <>
                  <p className="pt-2 text-sm font-medium">Missing keywords</p>
                  <p className="text-xs text-muted">
                    Add these to improve ATS match:{" "}
                    {resume.keywords_missing.map((k) => (
                      <Badge key={k} variant="warning" className="ml-1">{k}</Badge>
                    ))}
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <p className="mb-2 flex items-center gap-1.5 text-sm font-medium">
                <FileText className="h-4 w-4" /> How auto-updates work
              </p>
              <p className="text-xs leading-relaxed text-muted">
                The Resume agent pulls your active repositories and projects, rebuilds the
                document, and bumps the version number — keeping a full history. Run it from the
                terminal with <code className="font-mono text-[11px]">python manage.py run_agents resume</code>.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
