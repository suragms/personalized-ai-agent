import { useState } from "react";
import { FileDown, FileText, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/ui/empty-state";
import { MarkdownView } from "@/components/MarkdownView";
import { ProvenanceBadge } from "@/components/ProvenanceBadge";
import { useGenerateReport, useReports } from "@/hooks";
import { apiDownload } from "@/lib/api";
import { reports } from "@/services";
import { cn, shortDate } from "@/lib/utils";

const PERIODS = ["daily", "weekly", "monthly", "quarterly", "yearly", "internship", "client"] as const;

export default function Reports() {
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>("daily");
  const { data } = useReports(period);
  const generate = useGenerateReport();
  const reportsList = data?.results ?? [];

  async function onGenerate() {
    try {
      await generate.mutateAsync(period);
      toast.success(`${period} report generated`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Generation failed");
    }
  }

  function onExport(id: string, format: string, label: string) {
    void apiDownload(reports.exportUrl(id, format), `${period}-report.${format}`).catch(() => toast.error(`Export to ${label} failed`));
  }

  const selected = reportsList[0];

  return (
    <div>
      <PageHeader
        title="Reports"
        description="Daily, weekly, and monthly summaries with one-click exports."
        action={
          <Button onClick={onGenerate} disabled={generate.isPending}>
            <RefreshCw className={cn("h-4 w-4", generate.isPending && "animate-spin")} /> Generate {period} report
          </Button>
        }
      />

      <Tabs value={period} onValueChange={(v) => setPeriod(v as (typeof PERIODS)[number])}>
        <TabsList className="flex-wrap h-auto">
          {PERIODS.map((p) => (
            <TabsTrigger key={p} value={p} className="capitalize">
              {p}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={period}>
          {reportsList.length === 0 ? (
            <EmptyState title={`No ${period} reports yet`} description="Click 'Generate' to create one from your latest data." />
          ) : (
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
              <Card className="xl:col-span-2">
                <CardContent className="p-5">
                  {selected && (
                    <>
                      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
                        <div>
                          <p className="font-medium">{selected.title}</p>
                          <p className="text-xs text-muted">
                            {shortDate(selected.period_start)} → {shortDate(selected.period_end)} · generated {shortDate(selected.created_at)}
                          </p>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <ProvenanceBadge provenance={selected.provenance} />
                          <Badge variant="info">{selected.generated_by}</Badge>
                        </div>
                      </div>
                      <MarkdownView content={selected.content} className="max-h-[32rem] overflow-y-auto pr-2" />
                    </>
                  )}
                </CardContent>
              </Card>

              <div className="space-y-4">
                <Card>
                  <div className="p-4">
                    <p className="mb-3 text-sm font-medium">Exports</p>
                    <div className="flex flex-wrap gap-2">
                      {(
                        [
                          ["md", "Markdown"],
                          ["html", "HTML"],
                          ["pdf", "PDF"],
                          ["xlsx", "Excel"],
                          ["docx", "Word"],
                        ] as const
                      ).map(([fmt, label]) => (
                        <Button key={fmt} variant="secondary" size="sm" onClick={() => selected && onExport(selected.id, fmt, label)}>
                          <FileDown className="h-4 w-4" /> {label}
                        </Button>
                      ))}
                    </div>
                  </div>
                </Card>

                <Card>
                  <div className="p-4">
                    <p className="mb-3 text-sm font-medium">All {period} reports</p>
                    <div className="space-y-2">
                      {reportsList.map((r) => (
                        <div key={r.id} className="flex items-center justify-between gap-2 rounded-md border border-border/70 p-2 text-xs">
                          <span className="flex items-center gap-2 truncate">
                            <FileText className="h-3.5 w-3.5 text-muted" /> {shortDate(r.period_start)}
                          </span>
                          <Badge variant={r.id === selected?.id ? "primary" : "default"}>v</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
