import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { githubOAuth, intelligence } from "@/services/intelligence";

// ── GitHub OAuth Hooks ────────────────────────────────────────────────────
export function useGitHubStatus() {
  return useQuery({
    queryKey: ["github", "oauth", "status"],
    queryFn: githubOAuth.status,
    refetchInterval: 30000, // Refresh every 30s
  });
}

export function useGitHubSync() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: githubOAuth.syncNow,
    onSuccess: () => {
      // Invalidate all GitHub-related queries
      queryClient.invalidateQueries({ queryKey: ["github"] });
      queryClient.invalidateQueries({ queryKey: ["intelligence", "insights"] });
      queryClient.invalidateQueries({ queryKey: ["intelligence", "alerts"] });
      queryClient.invalidateQueries({ queryKey: ["intelligence", "data-sources"] });
    },
  });
}

export function useGitHubDisconnect() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: githubOAuth.disconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github"] });
      queryClient.invalidateQueries({ queryKey: ["intelligence", "integrations"] });
    },
  });
}

// ── Intelligence Hooks ────────────────────────────────────────────────────
export function useProfile() {
  return useQuery({
    queryKey: ["intelligence", "profile"],
    queryFn: intelligence.profile,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: intelligence.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intelligence", "profile"] });
    },
  });
}

export function useDataSources() {
  return useQuery({
    queryKey: ["intelligence", "data-sources"],
    queryFn: intelligence.dataSources,
  });
}

export function useInsights(params?: { status?: string; type?: string }) {
  return useQuery({
    queryKey: ["intelligence", "insights", params],
    queryFn: () => intelligence.insights(params),
  });
}

/** Aggregated engine counts + data health from GET /api/intelligence/summary/. */
export function useIntelligenceSummary() {
  return useQuery({
    queryKey: ["intelligence", "summary"],
    queryFn: intelligence.summary,
  });
}

export function useConvertInsightToTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => intelligence.convertInsightToTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intelligence"] });
      queryClient.invalidateQueries({ queryKey: ["productivity"] });
    },
  });
}

export function useMarkInsightHelpful() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, helpful }: { id: string; helpful: boolean }) =>
      intelligence.markInsightHelpful(id, helpful),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intelligence", "insights"] });
    },
  });
}

export function useDismissInsight() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => intelligence.dismissInsight(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intelligence", "insights"] });
    },
  });
}

export function useAlerts(params?: { status?: string }) {
  return useQuery({
    queryKey: ["intelligence", "alerts", params],
    queryFn: () => intelligence.alerts(params),
  });
}

export function useMarkAlertRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => intelligence.markAlertRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intelligence", "alerts"] });
    },
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => intelligence.resolveAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intelligence", "alerts"] });
    },
  });
}

export function useDailyPlan() {
  return useQuery({
    queryKey: ["intelligence", "daily-plan"],
    queryFn: intelligence.dailyPlan,
  });
}

export function useIntegrations() {
  return useQuery({
    queryKey: ["intelligence", "integrations"],
    queryFn: intelligence.integrations,
  });
}
