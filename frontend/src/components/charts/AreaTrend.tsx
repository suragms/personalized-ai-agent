import { useTheme } from "@/contexts/ThemeContext";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { chartInk, seriesColor } from "@/lib/chart";

interface Point {
  [key: string]: string | number;
}

interface AreaTrendProps {
  data: Point[];
  xKey?: string;
  series: { key: string; label: string; color?: string; dashed?: boolean }[];
  height?: number;
  showAxis?: boolean;
}

/** One-axis area/line chart with crosshair tooltip (dataviz: thin marks, 2px lines). */
export function AreaTrend({ data, xKey = "date", series, height = 220, showAxis = true }: AreaTrendProps) {
  const { theme } = useTheme();
  const dark = theme === "dark";
  const ink = chartInk(dark);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: showAxis ? -16 : 0 }}>
        <defs>
          {series.map((s) => (
            <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={s.color ?? seriesColor(series.indexOf(s), dark)} stopOpacity={0.32} />
              <stop offset="100%" stopColor={s.color ?? seriesColor(series.indexOf(s), dark)} stopOpacity={0.02} />
            </linearGradient>
          ))}
        </defs>
        {showAxis && <CartesianGrid vertical={false} stroke={ink.grid} />}
        <XAxis dataKey={xKey} tick={{ fill: ink.tick, fontSize: 11 }} axisLine={{ stroke: ink.axis }} tickLine={false} minTickGap={24} />
        {showAxis && <YAxis tick={{ fill: ink.tick, fontSize: 11 }} axisLine={false} tickLine={false} width={40} />}
        <Tooltip
          cursor={{ stroke: ink.axis, strokeDasharray: "4 4" }}
          contentStyle={{
            background: ink.surface,
            border: `1px solid ${ink.axis}`,
            borderRadius: 8,
            fontSize: 12,
            color: dark ? "#fff" : "#0b0b0b",
          }}
          labelStyle={{ color: ink.tick }}
        />
        {series.map((s) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={s.color ?? seriesColor(series.indexOf(s), dark)}
            strokeWidth={2}
            strokeDasharray={s.dashed ? "5 4" : undefined}
            fill={`url(#grad-${s.key})`}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
