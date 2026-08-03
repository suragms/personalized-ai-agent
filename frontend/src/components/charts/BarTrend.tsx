import { useTheme } from "@/contexts/ThemeContext";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { chartInk, seriesColor } from "@/lib/chart";

interface Point {
  [key: string]: string | number;
}

interface BarTrendProps {
  data: Point[];
  xKey: string;
  series: { key: string; label: string; color?: string }[];
  height?: number;
  stacked?: boolean;
}

/** Single-axis bar chart with per-mark hover (dataviz: 2px surface gap between bars). */
export function BarTrend({ data, xKey, series, height = 220, stacked }: BarTrendProps) {
  const { theme } = useTheme();
  const dark = theme === "dark";
  const ink = chartInk(dark);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }} barCategoryGap="28%">
        <CartesianGrid vertical={false} stroke={ink.grid} />
        <XAxis dataKey={xKey} tick={{ fill: ink.tick, fontSize: 11 }} axisLine={{ stroke: ink.axis }} tickLine={false} minTickGap={20} />
        <YAxis tick={{ fill: ink.tick, fontSize: 11 }} axisLine={false} tickLine={false} width={40} />
        <Tooltip
          cursor={{ fill: ink.grid, opacity: 0.4 }}
          contentStyle={{
            background: ink.surface,
            border: `1px solid ${ink.axis}`,
            borderRadius: 8,
            fontSize: 12,
            color: dark ? "#fff" : "#0b0b0b",
          }}
          labelStyle={{ color: ink.tick }}
        />
        {series.map((s, i) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.label}
            stackId={stacked ? "stack" : undefined}
            fill={s.color ?? seriesColor(i, dark)}
            radius={stacked ? [0, 0, 0, 0] : [4, 4, 0, 0]}
            maxBarSize={36}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
