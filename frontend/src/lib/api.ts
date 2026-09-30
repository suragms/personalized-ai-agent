import type { AuthTokens } from "@/types";

const ACCESS_KEY = "agent_access";
const REFRESH_KEY = "agent_refresh";

/**
 * API origin for cross-origin deployments (VITE_API_BASE).
 * Empty string in dev — the Vite dev server proxies /api and /ws to Django.
 */
const rawBase = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
export const API_BASE = rawBase.replace(/\/+$/, "");

/** Prefix a path with API_BASE (no-op when same-origin). */
export function buildUrl(path: string): string {
  if (!API_BASE) return path;
  return path.startsWith("/") ? `${API_BASE}${path}` : `${API_BASE}/${path}`;
}

/** Default per-request timeout so a hung server surfaces as TIMEOUT, not a freeze. */
const DEFAULT_TIMEOUT_MS = 20_000;

/**
 * Stable frontend error codes. Derived from the HTTP status (plus transport
 * failures); the backend's own snake_case code, when present, is preserved on
 * `serverCode`.
 */
export type ApiErrorCode =
  | "NETWORK_ERROR"
  | "TIMEOUT"
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "VALIDATION_ERROR"
  | "RATE_LIMITED"
  | "SERVER_ERROR"
  | "SERVICE_UNAVAILABLE"
  | "UNKNOWN_ERROR";

const FRIENDLY_MESSAGES: Record<ApiErrorCode, string> = {
  NETWORK_ERROR: "Can't reach the server. Check your connection and try again.",
  TIMEOUT: "The request timed out. The server may be busy — please try again.",
  UNAUTHORIZED: "Your session has expired. Please sign in again.",
  FORBIDDEN: "You don't have permission to do that.",
  NOT_FOUND: "That resource could not be found.",
  VALIDATION_ERROR: "Please check the fields and try again.",
  RATE_LIMITED: "Too many requests — please slow down and try again shortly.",
  SERVER_ERROR: "Something went wrong on the server.",
  SERVICE_UNAVAILABLE: "The service is temporarily unavailable.",
  UNKNOWN_ERROR: "Something went wrong.",
};

/** Typed error thrown by every api() helper. */
export class ApiError extends Error {
  readonly code: ApiErrorCode;
  readonly status: number;
  /** Raw server-provided code (snake_case), when the backend sent one. */
  readonly serverCode?: string;
  /** Raw server-provided detail message (already sanitized by the backend). */
  readonly detail?: string;
  /** True for failures worth retrying (network, timeout, 5xx, 429). */
  readonly retryable: boolean;

  constructor(
    code: ApiErrorCode,
    opts: { status?: number; message?: string; serverCode?: string; detail?: string; retryable?: boolean } = {},
  ) {
    super(opts.message || FRIENDLY_MESSAGES[code]);
    this.name = "ApiError";
    this.code = code;
    this.status = opts.status ?? 0;
    this.serverCode = opts.serverCode;
    this.detail = opts.detail;
    this.retryable = opts.retryable ?? (code === "NETWORK_ERROR" || code === "TIMEOUT" || code === "RATE_LIMITED" || code === "SERVER_ERROR" || code === "SERVICE_UNAVAILABLE");
  }
}

function codeForStatus(status: number): ApiErrorCode {
  if (status === 401) return "UNAUTHORIZED";
  if (status === 403) return "FORBIDDEN";
  if (status === 404) return "NOT_FOUND";
  if (status === 400 || status === 422) return "VALIDATION_ERROR";
  if (status === 429) return "RATE_LIMITED";
  if (status === 503) return "SERVICE_UNAVAILABLE";
  if (status >= 500) return "SERVER_ERROR";
  return "UNKNOWN_ERROR";
}

export function getAccess(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}
export function getRefresh(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}
export function setTokens(tokens: AuthTokens) {
  localStorage.setItem(ACCESS_KEY, tokens.access);
  localStorage.setItem(REFRESH_KEY, tokens.refresh);
}
export function setRawTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

/** Dispatched when the refresh token is definitively rejected (real logout). */
export const AUTH_EXPIRED_EVENT = "agent:auth-expired";

function authExpired() {
  clearTokens();
  window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
}

let refreshPromise: Promise<string | null> | null = null;

/**
 * Refresh the access token once (deduped across concurrent callers).
 *
 * Tokens are ONLY cleared when the server definitively rejects the refresh
 * token (4xx). Network errors and 5xx responses keep the session: an outage
 * must not silently log users out.
 */
async function refreshAccess(): Promise<string | null> {
  const refresh = getRefresh();
  if (!refresh) return null;
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(buildUrl("/api/auth/refresh/"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh }),
          credentials: "include",
          signal: AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
        });
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem(ACCESS_KEY, data.access);
          return data.access as string;
        }
        if (res.status >= 400 && res.status < 500) {
          // Definitive rejection: the refresh token is invalid or expired.
          authExpired();
        }
        // 5xx: transient — keep tokens and let the caller retry later.
        return null;
      } catch {
        // Network error / timeout: keep tokens (do NOT log the user out).
        return null;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

interface ApiOptions extends RequestInit {
  /** Override the request timeout (ms). */
  timeoutMs?: number;
}

async function fetchWithTimeout(path: string, options: ApiOptions): Promise<Response> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, signal, ...rest } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new DOMException("Timeout", "TimeoutError")), timeoutMs);
  // Respect a caller-provided signal as well.
  const onAbort = () => controller.abort(signal?.reason);
  if (signal) {
    if (signal.aborted) onAbort();
    else signal.addEventListener("abort", onAbort, { once: true });
  }
  try {
    return await fetch(buildUrl(path), { ...rest, signal: controller.signal, credentials: "include" });
  } catch (err) {
    if (controller.signal.aborted) {
      const reason = controller.signal.reason;
      if (reason instanceof DOMException && reason.name === "TimeoutError") {
        throw new ApiError("TIMEOUT", { retryable: true });
      }
      throw err; // caller-initiated abort — rethrow untouched
    }
    throw new ApiError("NETWORK_ERROR", { retryable: true });
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onAbort);
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  const code = codeForStatus(res.status);
  let detail: string | undefined;
  let serverCode: string | undefined;
  try {
    const body = await res.json();
    if (typeof body === "object" && body !== null) {
      if (typeof body.detail === "string") detail = body.detail;
      else if (typeof body.message === "string") detail = body.message;
      else {
        // Flatten DRF field errors:
        // {"email": ["Already exists."]} -> "email: Already exists."
        const errors = Object.entries(body)
          .map(([key, val]) => (Array.isArray(val) ? `${key}: ${val.join(" ")}` : `${key}: ${val}`))
          .join(" | ");
        if (errors) detail = errors;
      }
      if (typeof body.code === "string") serverCode = body.code;
    }
  } catch {
    /* non-JSON error body (e.g. HTML error page) — keep the friendly message */
  }
  const message = detail && res.status < 500 ? detail : undefined;
  return new ApiError(code, { status: res.status, message, detail, serverCode });
}

/** Typed fetch helper that attaches the JWT and retries once on 401. */
export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getAccess();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  let res: Response;
  try {
    res = await fetchWithTimeout(path, { ...options, headers });
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === "AbortError") {
      // Caller-cancelled — rethrow as-is so callers can ignore it.
      throw err;
    }
    throw new ApiError("NETWORK_ERROR", { retryable: true });
  }

  if (res.status === 401 && getRefresh()) {
    const newToken = await refreshAccess();
    if (newToken) {
      headers.set("Authorization", `Bearer ${newToken}`);
      res = await fetchWithTimeout(path, { ...options, headers });
    }
  }

  if (res.status === 204) return undefined as T;
  if (res.status >= 400) throw await toApiError(res);

  const contentType = res.headers.get("Content-Type") ?? "";
  if (contentType.includes("application/json")) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
}

/** Download a binary/attachment endpoint. */
export async function apiDownload(path: string, filename: string): Promise<void> {
  const headers = new Headers();
  const token = getAccess();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetchWithTimeout(path, { headers });
  if (!res.ok) throw await toApiError(res);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
