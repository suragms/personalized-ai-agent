import { Badge } from "@/components/ui/badge";

/**
 * Freshness badge — how old the data behind a value is (§10).
 *
 * Levels mirror the backend `compute_freshness` vocabulary:
 * fresh | aging | stale | unavailable. Stale and unavailable data are always
 * labelled as such so old numbers are never presented as current.
 */
const FRESHNESS: Record<string, { label: string; variant: "success" | "info" | "warning" | "critical"; title: string }> = {
  fresh: {
    label: "fresh",
    variant: "success",
    title: "Synchronized within the source's fresh window",
  },
  aging: {
    label: "aging",
    variant: "info",
    title: "Past the fresh window but still within the source's schedule",
  },
  stale: {
    label: "stale",
    variant: "warning",
    title: "Not synchronized recently — current values may differ",
  },
  unavailable: {
    label: "no data",
    variant: "critical",
    title: "This source has never been synchronized",
  },
};

export function FreshnessBadge({
  level,
  message,
}: {
  level?: string | null;
  /** Optional backend freshness message, shown as the badge tooltip. */
  message?: string | null;
}) {
  if (!level) return null;
  const entry = FRESHNESS[level.toLowerCase()] ?? {
    label: level,
    variant: "info" as const,
    title: `Freshness: ${level}`,
  };
  return (
    <Badge variant={entry.variant} title={message || entry.title}>
      {entry.label}
    </Badge>
  );
}
