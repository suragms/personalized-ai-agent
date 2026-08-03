/**
 * Validated categorical palette (dataviz method). Slot order is the
 * CVD-safety mechanism — assign hues in fixed order, never cycle.
 */
export const SERIES_HEX = {
  light: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"],
  dark: ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
} as const;

/** Status palette (fixed, never themed). */
export const STATUS_HEX = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
} as const;

/** Sequential ramp (blue) for magnitude encodings. */
export const SEQUENTIAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#184f95"];

/** The categorical color for slot `i` in the given mode (defaults to light). */
export function seriesColor(i: number, dark = false): string {
  return SERIES_HEX[dark ? "dark" : "light"][i % 8];
}

/** Theme-aware ink colors for chart chrome. */
export function chartInk(dark = false): { grid: string; axis: string; tick: string; surface: string } {
  return dark
    ? { grid: "#2c2c2a", axis: "#383835", tick: "#898781", surface: "#1a1a19" }
    : { grid: "#e1e0d9", axis: "#c3c2b7", tick: "#898781", surface: "#fcfcfb" };
}

/** Map a 0-100 score to its status tone name. */
export function statusTone(value: number): keyof typeof STATUS_HEX {
  if (value >= 75) return "good";
  if (value >= 50) return "serious";
  if (value >= 25) return "warning";
  return "critical";
}
