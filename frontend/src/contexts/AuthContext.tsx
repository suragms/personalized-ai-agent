import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { AUTH_EXPIRED_EVENT, ApiError, api, clearTokens, getAccess, setRawTokens, setTokens } from "@/lib/api";
import type { AuthTokens, User } from "@/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getAccess()) {
      setLoading(false);
      return;
    }
    try {
      const me = await api<User>("/api/auth/me/");
      setUser(me);
    } catch (err) {
      // Only treat a definitive rejection as logout — a network outage must
      // not wipe the session.
      if (err instanceof ApiError && (err.code === "UNAUTHORIZED" || err.code === "FORBIDDEN")) {
        clearTokens();
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // The API layer dispatches this only when the refresh token is rejected.
  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const res = await api<AuthTokens>("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setTokens(res);
    if (res.user) {
      setUser(res.user);
    } else {
      const me = await api<User>("/api/auth/me/");
      setUser(me);
    }
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, login, logout, refresh }), [user, loading, login, logout, refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

// Exported for tests / edge cases.
export { setRawTokens };
