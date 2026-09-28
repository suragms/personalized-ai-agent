import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { analytics, ai, github, learning, linkedin, notifications, portfolio, productivity, projects, providerConnections, reports, resume, skills } from "@/services";
import type { ProviderConnectionFormData, Task } from "@/types";

// ── Overview / analytics ──────────────────────────────────────────────────
export const useOverview = () => useQuery({ queryKey: ["overview"], queryFn: analytics.overview });

// ── GitHub ────────────────────────────────────────────────────────────────
export const useGithubAnalytics = (weeks = 8) => useQuery({ queryKey: ["github", "analytics", weeks], queryFn: () => github.analytics(weeks) });
export const useGithubRepos = () => useQuery({ queryKey: ["github", "repos"], queryFn: github.repos });
export const useGithubInsights = () => useQuery({ queryKey: ["github", "insights"], queryFn: github.insights });
export const useGithubContributions = () => useQuery({ queryKey: ["github", "contributions"], queryFn: () => github.contributions(90) });
export const useGithubHealth = () => useQuery({ queryKey: ["github", "health"], queryFn: github.health });

// ── Tasks / calendar / briefings ──────────────────────────────────────────
export const useTasks = (status?: string) => useQuery({ queryKey: ["tasks", status], queryFn: () => productivity.tasks(status) });
export const useUpdateTask = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Partial<Task> }) => productivity.updateTask(id, patch),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
};
export const useCalendar = () => useQuery({ queryKey: ["calendar"], queryFn: productivity.calendar });
export const useBriefing = (kind: "morning" | "eod") => useQuery({ queryKey: ["briefings", kind], queryFn: () => productivity.briefing(kind) });
export const useGenerateBriefing = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (kind: "morning" | "eod") => productivity.generateBriefing(kind),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["briefings"] }),
  });
};
export const useProductivityScore = () => useQuery({ queryKey: ["prod-score"], queryFn: productivity.score });

// ── Projects ──────────────────────────────────────────────────────────────
export const useProjects = () => useQuery({ queryKey: ["projects"], queryFn: projects.list });
export const useBurndown = () => useQuery({ queryKey: ["burndown"], queryFn: projects.burndown });

// ── Reports ───────────────────────────────────────────────────────────────
export const useReports = (period?: string) => useQuery({ queryKey: ["reports", period], queryFn: () => reports.list(period) });
export const useGenerateReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (period: string) => reports.generate(period),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["reports"] }),
  });
};

// ── Resume ────────────────────────────────────────────────────────────────
export const useResume = () => useQuery({ queryKey: ["resume"], queryFn: resume.latest, retry: false });
export const useRegenerateResume = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: resume.regenerate,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["resume"] }),
  });
};

// ── Portfolio ─────────────────────────────────────────────────────────────
export const usePortfolio = () => useQuery({ queryKey: ["portfolio"], queryFn: portfolio.projects });
export const useRefreshPortfolio = () => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: portfolio.refresh, onSuccess: () => void qc.invalidateQueries({ queryKey: ["portfolio"] }) });
};

// ── Learning ──────────────────────────────────────────────────────────────
export const useLearningItems = () => useQuery({ queryKey: ["learning", "items"], queryFn: learning.items });
export const useLearningSuggestions = () => useQuery({ queryKey: ["learning", "suggestions"], queryFn: learning.suggestions });
export const useLearningRoadmap = () => useQuery({ queryKey: ["learning", "roadmap"], queryFn: learning.roadmap });
export const useLearningTrends = () => useQuery({ queryKey: ["learning", "trends"], queryFn: learning.trends });
export const useCompleteLearningItem = () => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: learning.completeItem, onSuccess: () => void qc.invalidateQueries({ queryKey: ["learning"] }) });
};

// ── LinkedIn ──────────────────────────────────────────────────────────────
export const useLinkedinProfile = () => useQuery({ queryKey: ["linkedin", "profile"], queryFn: linkedin.profile });
export const useLinkedinAnalyze = () => useQuery({ queryKey: ["linkedin", "analyze"], queryFn: linkedin.analyze });
export const useLinkedinPosts = () => useQuery({ queryKey: ["linkedin", "posts"], queryFn: linkedin.posts });
export const useGeneratePost = () => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: linkedin.generatePost, onSuccess: () => void qc.invalidateQueries({ queryKey: ["linkedin", "posts"] }) });
};
export const usePostingTime = () => useQuery({ queryKey: ["linkedin", "posting-time"], queryFn: linkedin.postingTime });

// ── Notifications ─────────────────────────────────────────────────────────
export const useNotifications = () => useQuery({ queryKey: ["notifications"], queryFn: notifications.list });
export const useUnread = () => useQuery({ queryKey: ["unread"], queryFn: notifications.unread, refetchInterval: 30_000 });
export const useMarkAllRead = () => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: notifications.markAllRead, onSuccess: () => void qc.invalidateQueries({ queryKey: ["notifications"] }) });
};
export const useSweep = () => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: notifications.sweep, onSuccess: () => void qc.invalidateQueries({ queryKey: ["notifications"] }) });
};

// ── AI assistant ──────────────────────────────────────────────────────────
export const useAiCommand = () => useMutation({ mutationFn: ai.command });
export const useProviders = () => useQuery({ queryKey: ["providers"], queryFn: ai.providers });

// ── Provider Connections (user-scoped) ────────────────────────────────────
export const useProviderConnections = () =>
  useQuery({ queryKey: ["provider-connections"], queryFn: providerConnections.list });

export const useProviderDefinitions = () =>
  useQuery({ queryKey: ["provider-definitions"], queryFn: providerConnections.definitions });

export const useCreateProviderConnection = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProviderConnectionFormData) => providerConnections.create(data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["provider-connections"] }),
  });
};

export const useUpdateProviderConnection = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ProviderConnectionFormData> }) =>
      providerConnections.update(id, data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["provider-connections"] }),
  });
};

export const useDeleteProviderConnection = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => providerConnections.delete(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["provider-connections"] }),
  });
};

export const useTestProviderConnection = () =>
  useMutation({ mutationFn: (id: string) => providerConnections.test(id) });

// ── Skills ────────────────────────────────────────────────────────────────
export const useSkills = () => useQuery({ queryKey: ["skills"], queryFn: skills.list });

export const useEnableSkill = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => skills.enable(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["skills"] }),
  });
};

export const useDisableSkill = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => skills.disable(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["skills"] }),
  });
};

export const useValidateSkill = () =>
  useMutation({ mutationFn: (id: string) => skills.validate(id) });

export const useTestSkill = () =>
  useMutation({ mutationFn: ({ id, context }: { id: string; context?: string }) => skills.test(id, context) });

export const useSkillExecutions = () =>
  useQuery({ queryKey: ["skill-executions"], queryFn: skills.executions });
