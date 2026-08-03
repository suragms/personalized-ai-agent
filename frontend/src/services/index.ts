import { api } from "@/lib/api";
import type {
  Briefing,
  CalendarEvent,
  CommandResult,
  Commit,
  ContributionPoint,
  GithubAnalytics,
  GithubInsight,
  LearningItem,
  LearningRoadmap,
  LearningSuggestion,
  LinkedInProfile,
  LinkedInScore,
  Notification,
  Overview,
  PortfolioProject,
  PostIdea,
  Project,
  Report,
  Repository,
  ResumeVersion,
  Task,
} from "@/types";

// ── Auth ──────────────────────────────────────────────────────────────────
export const auth = {
  login: (username: string, password: string) =>
    api<{ access: string; refresh: string; user: unknown }>("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
};

// ── Overview / analytics ──────────────────────────────────────────────────
export const analytics = {
  overview: () => api<Overview>("/api/analytics/overview/"),
};

// ── GitHub ────────────────────────────────────────────────────────────────
export const github = {
  repos: () => api<{ results: Repository[] }>("/api/github/repos/"),
  analytics: (weeks = 8) => api<GithubAnalytics>(`/api/github/analytics/?weeks=${weeks}`),
  health: () => api<{ repositories: { name: string; status: string; last_commit_days: number }[] }>("/api/github/health/"),
  insights: () => api<GithubInsight[]>("/api/github/insights/"),
  contributions: (days = 90) => api<ContributionPoint[]>(`/api/github/contributions/?days=${days}`),
  commits: (repo?: string) => api<{ results: Commit[] }>(`/api/github/commits/${repo ? `?repository=${encodeURIComponent(repo)}` : ""}`),
};

// ── Tasks / calendar / briefings ──────────────────────────────────────────
export const productivity = {
  tasks: (status?: string) => api<{ results: Task[] }>(`/api/tasks/${status ? `?status=${status}` : ""}`),
  updateTask: (id: string, patch: Partial<Task>) => api<Task>(`/api/tasks/${id}/`, { method: "PATCH", body: JSON.stringify(patch) }),
  createTask: (task: Partial<Task>) => api<Task>("/api/tasks/", { method: "POST", body: JSON.stringify(task) }),
  calendar: () => api<{ results: CalendarEvent[] }>("/api/calendar/"),
  briefing: (kind: "morning" | "eod") => api<{ results: Briefing[] }>(`/api/briefings/?kind=${kind}`),
  generateBriefing: (kind: "morning" | "eod") => api<Briefing>("/api/briefings/generate/", { method: "POST", body: JSON.stringify({ kind }) }),
  score: () => api<{ date: string; productivity_score: number }>("/api/productivity/score/"),
};

// ── Projects ──────────────────────────────────────────────────────────────
export const projects = {
  list: () => api<{ results: Project[] }>("/api/projects/"),
  burndown: () => api<{ id: string; name: string; series: { date: string; remaining: number }[] }[]>("/api/projects/burndown/overview/"),
};

// ── Reports ───────────────────────────────────────────────────────────────
export const reports = {
  list: (period?: string) => api<{ results: Report[] }>(`/api/reports/${period ? `?period=${period}` : ""}`),
  generate: (period: string) => api<Report>("/api/reports/generate/", { method: "POST", body: JSON.stringify({ period }) }),
  exportUrl: (id: string, format: string) => `/api/reports/${id}/export/?format=${format}`,
};

// ── Resume ────────────────────────────────────────────────────────────────
export const resume = {
  latest: () => api<ResumeVersion>("/api/resume/latest/"),
  regenerate: () => api<ResumeVersion>("/api/resume/versions/regenerate/", { method: "POST" }),
  exportUrl: (id: string, format: string) => `/api/resume/versions/${id}/export/?format=${format}`,
};

// ── Portfolio ─────────────────────────────────────────────────────────────
export const portfolio = {
  projects: () => api<{ results: PortfolioProject[] }>("/api/portfolio/projects/"),
  refresh: () => api<PortfolioProject[]>("/api/portfolio/projects/refresh/", { method: "POST" }),
};

// ── Learning ──────────────────────────────────────────────────────────────
export const learning = {
  items: () => api<{ results: LearningItem[] }>("/api/learning/items/"),
  suggestions: () => api<LearningSuggestion[]>("/api/learning/suggestions/"),
  roadmap: () => api<LearningRoadmap>("/api/learning/roadmap/"),
  trends: () => api<{ trends: { title: string; kind: string; reason: string }[] }>("/api/learning/trends/"),
  completeItem: (id: string) => api<LearningItem>(`/api/learning/items/${id}/complete/`, { method: "POST" }),
};

// ── LinkedIn ──────────────────────────────────────────────────────────────
export const linkedin = {
  profile: () => api<LinkedInProfile>("/api/linkedin/profile/"),
  analyze: () => api<LinkedInScore>("/api/linkedin/analyze/"),
  posts: () => api<{ results: PostIdea[] }>("/api/linkedin/posts/"),
  generatePost: () => api<PostIdea>("/api/linkedin/posts/generate/", { method: "POST" }),
  postingTime: () => api<{ windows: { window: string; reason: string }[]; reason: string }>("/api/linkedin/posting-time/"),
};

// ── Notifications ─────────────────────────────────────────────────────────
export const notifications = {
  list: () => api<{ results: Notification[] }>("/api/notifications/"),
  unread: () => api<{ unread: number }>("/api/notifications/unread/"),
  markAllRead: () => api<{ updated: number }>("/api/notifications/mark_all_read/", { method: "POST" }),
  sweep: () => api<{ created: number }>("/api/notifications/sweep/", { method: "POST" }),
};

// ── AI command ────────────────────────────────────────────────────────────
export const ai = {
  command: (command: string) => api<CommandResult>("/api/ai/command/", { method: "POST", body: JSON.stringify({ command }) }),
  providers: () => api<{ providers: { name: string; active: boolean; available: boolean }[] }>("/api/ai/providers/"),
};
