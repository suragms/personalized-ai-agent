import { useTheme } from "@/contexts/ThemeContext";
import { ResponsiveContainer, RadialBar, RadialBarChart } from "recharts";
import { chartInk, seriesColor, statusTone } from "@/lib/chart";

interface RadialScoreProps {
  value: number; // 0-100
  label?: string;
  size?: number;
}

/** Radial gauge for a single headline score (productivity, ATS, LinkedIn). */
export function RadialScore({ value, label, size = 150 }: RadialScoreProps) {
  const { theme } = useTheme();
  const dark = theme === "dark";
  const ink = chartInk(dark);
  const clamped = Math.max(0, Math.min(100, value));
  const color = value >= 0 ? statusTone(clamped) : "warning";
  const statusColor = { good: "#0ca30c", warning: "#fab219", serious: "#ec835a", critical: "#d03b3b" }[color] ?? seriesColor(0, dark);

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart innerRadius="78%" outerRadius="100%" data={[{ value: clamped }]} startAngle={90} endAngle={-270}>
          <RadialBar dataKey="value" fill={statusColor} cornerRadius={8} background={{ fill: ink.grid }} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-semibold tabular-nums" style={{ color: ink.surface === "#fcfcfb" ? "#0b0b0b" : "#ffffff" }}>
          {Math.round(clamped)}
        </span>
        {label && <span className="text-[11px] text-muted">{label}</span>}
      </div>
    </div>
  );
}
