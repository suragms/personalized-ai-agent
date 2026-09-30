import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { Toaster, toast } from "sonner";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api";
import App from "@/App";
import "@/index.css";

/** Never surface caller-cancelled requests (component unmount, refetch, …). */
function isCancellation(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

// Deduplicate identical error toasts (e.g. many queries failing at once while
// the server is down would otherwise spam one toast per query).
const recentErrors = new Map<string, number>();
function notifyError(error: unknown) {
  if (isCancellation(error)) return;
  const message = errorMessage(error);
  const now = Date.now();
  const last = recentErrors.get(message) ?? 0;
  if (now - last < 4000) return;
  recentErrors.set(message, now);
  // Housekeeping so the map cannot grow unbounded.
  if (recentErrors.size > 50) {
    for (const [key, at] of recentErrors) {
      if (now - at > 10_000) recentErrors.delete(key);
    }
  }
  toast.error(message);
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({ onError: notifyError }),
  mutationCache: new MutationCache({ onError: notifyError }),
  defaultOptions: {
    queries: {
      // Retry transient failures (network/timeout/5xx) a little harder;
      // never retry definitive 4xx errors.
      retry: (failureCount, error) => {
        if (error instanceof ApiError && !error.retryable) return false;
        return failureCount < 2;
      },
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider delayDuration={150}>
          <AuthProvider>
            <BrowserRouter>
              <App />
              <Toaster position="top-right" richColors />
            </BrowserRouter>
          </AuthProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);
