/**
 * Canonical connectivity-status helpers.
 *
 * Mirrors the backend vocabulary (`core.connectivity.ConnectivityStatus`):
 * wire values are lowercase snake_case, but legacy rows and older code may
 * still hold UPPERCASE or alias spellings — always read through
 * `normalizeStatus()` before comparing.
 */

/** Legacy / alternate spellings accepted on read (never written). */
const ALIASES: Record<string, string> = {
  ok: "connected",
  active: "connected",
  authorized: "connected",
  healthy: "connected",
  success: "connected",
  syncing: "connecting",
  pending: "connecting",
  expired: "authentication_failed",
  unauthorized: "authentication_failed",
  revoked: "disconnected",
  offline: "disconnected",
  disabled: "disconnected",
  error: "api_error",
  failed: "api_error",
  unavailable: "service_unavailable",
  missing: "not_configured",
  unconfigured: "not_configured",
};

/** Normalize any stored/legacy status spelling to the canonical value. */
export function normalizeStatus(value?: string | null): string {
  if (!value) return "unknown_error";
  const v = value.trim().toLowerCase();
  return ALIASES[v] ?? v;
}

/** "authentication_failed" -> "Authentication Failed" */
export function statusLabel(value?: string | null): string {
  const s = normalizeStatus(value);
  return s
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export type StatusTone = "success" | "warning" | "critical" | "info" | "default";

const TONES: Record<string, StatusTone> = {
  connected: "success",
  running: "success",
  configured: "success",
  fresh: "success",
  connecting: "info",
  no_data: "info",
  stale: "warning",
  // Not-connected/not-configured is a neutral state, not a warning.
  disconnected: "default",
  not_configured: "default",
  rate_limited: "warning",
  timeout: "warning",
  network_error: "warning",
  service_unavailable: "warning",
  data_unavailable: "warning",
  authentication_failed: "critical",
  invalid_credentials: "critical",
  permission_denied: "critical",
  api_error: "critical",
  unknown_error: "critical",
};

/** Badge variant tone for a status value. */
export function statusTone(value?: string | null): StatusTone {
  return TONES[normalizeStatus(value)] ?? "default";
}

/** True for statuses where a retry can plausibly succeed. */
export function isRetryableStatus(value?: string | null): boolean {
  return ["rate_limited", "timeout", "network_error", "service_unavailable", "connecting"].includes(
    normalizeStatus(value),
  );
}
