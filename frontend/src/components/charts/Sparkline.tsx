import { useTheme } from "@/contexts/ThemeContext";
import { seriesColor } from "@/lib/chart";

/** Minimal trend sparkline with no axes — for KPI tiles. */
export function Sparkline({ data, color }: { data: number[]; color?: string }) {
  const { theme } = useTheme();
  const dark = theme === "dark";
  const fill = color ?? seriesColor(0, dark);

  if (data.length < 2) return null;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const w = 100;
  const h = 28;
  const step = w / (data.length - 1);
  const points = data.map((v, i) => `${(i * step).toFixed(1)},${(h - ((v - min) / range) * (h - 4) - 2).toFixed(1)}`).join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-7 w-full" aria-hidden>
      <polyline points={points} fill="none" stroke={fill} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
