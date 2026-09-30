import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, api, getRefresh, setRawTokens } from "./api";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api() error handling", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("maps 500 to a retryable SERVER_ERROR without leaking internals", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(500, { detail: "Traceback: secret internals" }));

    const err = (await api("/api/x/").catch((e) => e)) as ApiError;

    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("SERVER_ERROR");
    expect(err.status).toBe(500);
    expect(err.retryable).toBe(true);
    expect(err.message).not.toContain("Traceback");
  });

  it("surfaces 400 validation details as VALIDATION_ERROR", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(400, { username: ["Already exists."] }));

    const err = (await api("/api/x/", { method: "POST", body: "{}" }).catch((e) => e)) as ApiError;

    expect(err.code).toBe("VALIDATION_ERROR");
    expect(err.message).toContain("Already exists.");
    expect(err.retryable).toBe(false);
  });

  it("maps network failures to NETWORK_ERROR and keeps the session", async () => {
    setRawTokens("access-token", "refresh-token");
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));

    const err = (await api("/api/x/").catch((e) => e)) as ApiError;

    expect(err.code).toBe("NETWORK_ERROR");
    expect(err.retryable).toBe(true);
    expect(getRefresh()).toBe("refresh-token");
  });

  it("clears tokens only when the refresh token is definitively rejected", async () => {
    setRawTokens("expired-access", "refresh-token");
    const onExpired = vi.fn();
    window.addEventListener("agent:auth-expired", onExpired, { once: true });

    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Token expired" }))
      .mockResolvedValueOnce(jsonResponse(400, { detail: "Token is invalid or expired" }));

    const err = (await api("/api/x/").catch((e) => e)) as ApiError;

    expect(err.code).toBe("UNAUTHORIZED");
    expect(getRefresh()).toBeNull();
    expect(onExpired).toHaveBeenCalled();
  });

  it("keeps tokens when the refresh endpoint is unreachable (outage ≠ logout)", async () => {
    setRawTokens("expired-access", "refresh-token");

    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Token expired" }))
      .mockRejectedValueOnce(new TypeError("Failed to fetch"));

    const err = (await api("/api/x/").catch((e) => e)) as ApiError;

    expect(err.code).toBe("UNAUTHORIZED");
    expect(getRefresh()).toBe("refresh-token");
  });

  it("turns hung requests into TIMEOUT", async () => {
    globalThis.fetch = vi.fn(
      (_url: unknown, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(init.signal?.reason));
        }),
    );

    const err = (await api("/api/x/", { timeoutMs: 20 }).catch((e) => e)) as ApiError;

    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("TIMEOUT");
    expect(err.retryable).toBe(true);
  });

  it("sends cookies with credentials: include", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }));

    await api("/api/x/");

    const [, init] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(init.credentials).toBe("include");
  });

  it("retries once with a fresh token after a 401", async () => {
    setRawTokens("expired-access", "refresh-token");
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(jsonResponse(200, { access: "new-access" })) // refresh
      .mockResolvedValueOnce(jsonResponse(200, { ok: true })); // retried request

    const result = await api<{ ok: boolean }>("/api/x/");

    expect(result.ok).toBe(true);
    expect(localStorage.getItem("agent_access")).toBe("new-access");
    expect(globalThis.fetch).toHaveBeenCalledTimes(3);
  });
});
