import { useState } from "react";
import { TrendingUp, Filter, X, ThumbsUp, ThumbsDown, AlertCircle, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProvenanceBadge } from "@/components/ProvenanceBadge";
import { useInsights, useMarkInsightHelpful, useDismissInsight, useConvertInsightToTask } from "@/hooks/useIntelligence";
import type { Insight } from "@/services/intelligence";
import { cn } from "@/lib/utils";

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

const SEVERITY_VARIANT: Record<string, "critical" | "warning" | "info" | "success" | "default"> = {
  critical: "critical",
  high: "warning",
  medium: "warning",
  low: "info",
  info: "info",
};

const TYPE_LABELS: Record<string, string> = {
  observation: "Observation",
  trend: "Trend",
  opportunity: "Opportunity",
  risk: "Risk",
  blocker: "Blocker",
  improvement: "Improvement",
};

export default function Insights() {
  const [filterStatus, setFilterStatus] = useState<string>("active");
  const [filterType, setFilterType] = useState<string>("");
  const [filterSeverity, setFilterSeverity] = useState<string>("");
  const [selected, setSelected] = useState<Insight | null>(null);

  const { data, isLoading, isError, error } = useInsights({
    status: filterStatus || undefined,
    type: filterType || undefined,
  });

  const markHelpful = useMarkInsightHelpful();
  const dismiss = useDismissInsight();

  const insights = data?.results ?? [];

  // Apply severity filter client-side (API may not support it)
  const filtered = filterSeverity
    ? insights.filter((i) => i.severity === filterSeverity)
    : insights;

  // Sort by severity
  const sorted = [...filtered].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 5) - (SEVERITY_ORDER[b.severity] ?? 5)
  );

  return (
    <div>
      <PageHeader
        title="Insights"
        description="Evidence-based recommendations from your connected data sources."
      />

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Filter className="h-4 w-4 text-muted" />

        <div className="flex gap-1">
          {["active", "new", "reviewed", "expired", "dismissed"].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStatus(s === filterStatus ? "" : s)}
              className={cn(
                "rounded-full border px-3 py-0.5 text-xs font-medium capitalize transition-colors",
                filterStatus === s
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

        <div className="h-4 w-px bg-border" />

        <div className="flex gap-1">
          {Object.entries(TYPE_LABELS).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setFilterType(key === filterType ? "" : key)}
              className={cn(
                "rounded-full border px-3 py-0.5 text-xs font-medium transition-colors",
                filterType === key
                  ? "border-primary/60 bg-primary/10 text-primary"
                  : "border-border text-muted hover:border-primary/30"
              )}
            >
              {label}
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
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-1/2" />
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
            <p className="font-medium text-red-500">Failed to load insights</p>
            <p className="mt-1 text-sm text-muted">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && sorted.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-border bg-muted/5 px-6 py-12 text-center">
          <TrendingUp className="h-10 w-10 text-muted" />
          <div>
            <p className="font-medium">No insights available</p>
            <p className="mt-1 text-sm text-muted">
              {filterStatus || filterType || filterSeverity
                ? "No insights match the current filters."
                : "Connect data sources and run a sync to generate insights."}
            </p>
          </div>
          {(filterStatus || filterType || filterSeverity) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setFilterStatus("");
                setFilterType("");
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
        <div className="grid gap-3 lg:grid-cols-2">
          {sorted.map((insight) => (
            <InsightCard
              key={insight.id}
              insight={insight}
              onSelect={() => setSelected(insight)}
              onMarkHelpful={(helpful) => markHelpful.mutate({ id: insight.id, helpful })}
              onDismiss={() => dismiss.mutate(insight.id)}
              isPending={markHelpful.isPending || dismiss.isPending}
            />
          ))}
        </div>
      )}

      {/* Detail panel */}
      {selected && (
        <InsightDetail insight={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}

function InsightCard({
  insight,
  onSelect,
  onMarkHelpful,
  onDismiss,
  isPending,
}: {
  insight: Insight;
  onSelect: () => void;
  onMarkHelpful: (helpful: boolean) => void;
  onDismiss: () => void;
  isPending: boolean;
}) {
  return (
    <Card
      className={cn(
        "cursor-pointer transition-shadow hover:shadow-md",
        (insight.status === "dismissed" || insight.status === "expired") && "opacity-60"
      )}
      onClick={onSelect}
    >
      <CardHeader className="pb-2 flex-row items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-1.5 mb-1">
            <Badge variant={SEVERITY_VARIANT[insight.severity] ?? "default"}>
              {insight.severity}
            </Badge>
            <Badge variant="default">{TYPE_LABELS[insight.insight_type] ?? insight.insight_type}</Badge>
            <Badge variant={insight.confidence === "high" ? "success" : "info"} className="text-[10px]">
              {insight.confidence} confidence
            </Badge>
            <ProvenanceBadge provenance={insight.provenance} />
          </div>
          <CardTitle className="text-sm leading-snug">{insight.title}</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        <p className="text-xs text-muted line-clamp-2">{insight.description}</p>

        {insight.recommended_action && (
          <div className="rounded bg-primary/5 px-2 py-1.5 text-xs">
            <span className="font-medium text-primary">Recommendation: </span>
            <span className="text-muted">{insight.recommended_action}</span>
          </div>
        )}

        <div className="flex items-center justify-between pt-1">
          <p className="text-[10px] text-muted">
            {new Date(insight.created_at).toLocaleDateString()}
            {insight.source_references.length > 0 && " · has evidence"}
            {insight.last_confirmed_at && ` · confirmed ${new Date(insight.last_confirmed_at).toLocaleDateString()}`}
          </p>
          <div
            className="flex items-center gap-1"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => onMarkHelpful(true)}
              disabled={isPending}
              className={cn(
                "rounded p-1 text-muted hover:text-green-500 transition-colors",
                insight.helpful === true && "text-green-500"
              )}
              aria-label="Mark helpful"
            >
              <ThumbsUp className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => onMarkHelpful(false)}
              disabled={isPending}
              className={cn(
                "rounded p-1 text-muted hover:text-red-500 transition-colors",
                insight.helpful === false && "text-red-500"
              )}
              aria-label="Mark not helpful"
            >
              <ThumbsDown className="h-3.5 w-3.5" />
            </button>
            {insight.status !== "dismissed" && (
              <button
                onClick={onDismiss}
                disabled={isPending}
                className="rounded p-1 text-muted hover:text-foreground transition-colors"
                aria-label="Dismiss"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function InsightDetail({ insight, onClose }: { insight: Insight; onClose: () => void }) {
  const interpretationMeta = insight.interpretation_meta;
  const hasInterpretation = Boolean(insight.ai_interpretation) && interpretationMeta?.available === true;
  const interpretationAttempted = Boolean(interpretationMeta?.generated_at);
  const convert = useConvertInsightToTask();
  const canConvert =
    Boolean(insight.recommended_action) &&
    !["dismissed", "completed", "converted_to_task"].includes(insight.status);

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl rounded-xl border border-border bg-background shadow-xl overflow-y-auto max-h-[90vh]">
        <div className="flex items-start justify-between gap-3 p-5 border-b border-border">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap gap-1.5 mb-2">
              <Badge variant={SEVERITY_VARIANT[insight.severity] ?? "default"}>{insight.severity}</Badge>
              <Badge variant="default">{TYPE_LABELS[insight.insight_type] ?? insight.insight_type}</Badge>
              <ProvenanceBadge provenance={insight.provenance} />
            </div>
            <h2 className="text-base font-semibold leading-snug">{insight.title}</h2>
          </div>
          <button onClick={onClose} className="text-muted hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 p-5">
          <Section title="Summary">
            <p className="text-sm text-muted">{insight.summary || insight.description}</p>
          </Section>

          <Section title="AI Interpretation">
            {hasInterpretation ? (
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-primary" />
                  <ProvenanceBadge provenance={interpretationMeta?.provenance ?? "REAL_AI_PROVIDER"} />
                </div>
                <p className="text-sm text-muted">{insight.ai_interpretation}</p>
              </div>
            ) : interpretationAttempted ? (
              <p className="text-xs text-muted">
                AI interpretation unavailable ({interpretationMeta?.provenance ?? "provider unavailable"}).
                The deterministic evidence below stands on its own — nothing was generated to fill this space.
              </p>
            ) : (
              <p className="text-xs text-muted">Not interpreted yet — interpretation runs with the next engine pass.</p>
            )}
          </Section>

          <Section title="Priority">
            <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
              <Badge variant={SEVERITY_VARIANT[insight.priority] ?? "default"}>{insight.priority} priority</Badge>
            </div>
            {insight.priority_reasoning?.length > 0 ? (
              <ul className="space-y-1">
                {insight.priority_reasoning.map((factor) => (
                  <li key={factor.name} className="text-xs text-muted">
                    <strong className="text-foreground">{factor.name}</strong> ({factor.points > 0 ? "+" : ""}
                    {factor.points}): {factor.reason}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-muted">No priority factors recorded.</p>
            )}
          </Section>

          {insight.evidence && (
            <Section title="Evidence">
              <pre className="rounded bg-muted/10 p-3 text-xs text-muted whitespace-pre-wrap font-mono">
                {insight.evidence}
              </pre>
            </Section>
          )}

          {insight.structured_evidence?.length > 0 && (
            <Section title="Structured Evidence">
              <ul className="space-y-1">
                {insight.structured_evidence.map((entry, idx) => (
                  <li key={idx} className="text-xs text-muted">
                    {Object.entries(entry)
                      .map(([k, v]) => `${k}: ${String(v)}`)
                      .join(" · ")}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {insight.recommended_action && (
            <Section title="Recommendation">
              <p className="text-sm text-muted">{insight.recommended_action}</p>
            </Section>
          )}

          <Section title="Provenance">
            <div className="flex flex-wrap items-center gap-1.5">
              <ProvenanceBadge provenance={insight.provenance} />
              {insight.source_type && <Badge variant="default">{insight.source_type}</Badge>}
              {insight.snapshot && <Badge variant="info">snapshot linked</Badge>}
            </div>
            {(insight.provenance === "STALE_DATA" || insight.provenance === "UNAVAILABLE_DATA") && (
              <p className="mt-1.5 text-xs text-muted">
                This finding was computed from data that is not currently fresh — treat values as indicative.
              </p>
            )}
            {insight.last_confirmed_at && (
              <p className="mt-1.5 text-[11px] text-muted">
                Last confirmed by the engine: {new Date(insight.last_confirmed_at).toLocaleString()}
              </p>
            )}
          </Section>

          {insight.source_references.length > 0 && (
            <Section title="Source References">
              <pre className="rounded bg-muted/10 p-3 text-xs text-muted whitespace-pre-wrap font-mono">
                {JSON.stringify(insight.source_references, null, 2)}
              </pre>
            </Section>
          )}

          <div className="flex flex-wrap gap-3 text-xs text-muted">
            <span>Confidence: <strong>{insight.confidence}</strong></span>
            <span>Status: <strong>{insight.status}</strong></span>
            <span>Created: <strong>{new Date(insight.created_at).toLocaleString()}</strong></span>
            {insight.expires_at && (
              <span>Expires: <strong>{new Date(insight.expires_at).toLocaleString()}</strong></span>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            {canConvert && (
              <Button
                size="sm"
                disabled={convert.isPending}
                onClick={() =>
                  convert.mutate(insight.id, {
                    onSuccess: () => toast.success("Recommendation converted to task"),
                    onError: (err) => toast.error(err instanceof Error ? err.message : "Conversion failed"),
                  })
                }
              >
                {convert.isPending ? "Converting…" : "Convert to task"}
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
          </div>
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
