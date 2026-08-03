import { useMemo } from "react";
import { useTheme } from "@/contexts/ThemeContext";
import { SEQUENTIAL } from "@/lib/chart";
import type { ContributionPoint } from "@/types";

/** GitHub-style contribution grid (sequential blue ramp, cell-based tooltip via title). */
export function ContributionHeatmap({ data }: { data: ContributionPoint[] }) {
  const { theme } = useTheme();
  const dark = theme === "dark";

  const weeks = useMemo(() => {
    const rows: ContributionPoint[][] = [];
    let week: ContributionPoint[] = [];
    for (const point of data) {
      week.push(point);
      if (week.length === 7) {
        rows.push(week);
        week = [];
      }
    }
    if (week.length) rows.push(week);
    return rows;
  }, [data]);

  const max = Math.max(...data.map((d) => d.commits), 1);

  function cellColor(count: number): string {
    if (count === 0) return dark ? "#1f2540" : "#edeff6";
    const idx = Math.min(SEQUENTIAL.length - 1, Math.floor((count / max) * SEQUENTIAL.length));
    return SEQUENTIAL[idx];
  }

  return (
    <div className="overflow-x-auto">
      <div className="flex gap-[3px]" role="img" aria-label="Commit contribution heatmap">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-[3px]">
            {Array.from({ length: 7 }).map((_, di) => {
              const point = week[di];
              return (
                <div
                  key={di}
                  title={point ? `${point.date}: ${point.commits} commit${point.commits === 1 ? "" : "s"}` : ""}
                  className="h-[11px] w-[11px] rounded-[3px] transition-transform hover:scale-125"
                  style={{ background: point ? cellColor(point.commits) : "transparent" }}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
