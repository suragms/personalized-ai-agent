import { api } from "@/lib/api";

// ── Intelligence Types ────────────────────────────────────────────────────
export interface DataSource {
  id: string;
  source_type: string;
  name: string;
  url: string;
  state: "connected" | "syncing" | "disconnected" | "error" | "stale" | "unavailable";
  last_synced_at: string | null;
  last_error: string;
  sync_frequency_hours: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Insight {
  id: string;
  insight_type: "observation" | "trend" | "opportunity" | "risk" | "blocker" | "improvement";
  severity: "info" | "low" | "medium" | "high" | "critical";
  confidence: "low" | "medium" | "high";
  title: string;
  description: string;
  evidence: string;
  source_references: Record<string, unknown>[];
  recommended_action: string;
  status: "new" | "reviewed" | "accepted" | "dismissed" | "converted_to_task" | "completed";
  expires_at: string | null;
  helpful: boolean | null;
  user_notes: string;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  category: string;
  severity: "info" | "low" | "medium" | "high" | "critical";
  title: string;
  message: string;
  evidence: string;
  source_type: string;
  action_url: string;
  status: "active" | "read" | "resolved" | "dismissed";
  read_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  onboarding_completed: boolean;
  onboarding_step: string;
  professional_title: string;
  bio: string;
  github_url: string;
  portfolio_url: string;
  linkedin_url: string;
  instagram_url: string;
  facebook_url: string;
  twitter_url: string;
  other_urls: string[];
  timezone: string;
  working_hours_start: string | null;
  working_hours_end: string | null;
  working_days: number[];
  primary_goals: string[];
  current_priorities: string[];
  preferred_ai_behavior: string;
  notification_preferences: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface IntegrationConnection {
  id: string;
  platform: string;
  status: "connected" | "expired" | "error" | "disconnected";
  connected_account: string;
  scopes: string[];
  last_synced_at: string | null;
  last_error: string;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface GitHubOAuthStatus {
  connected: boolean;
  status: "connected" | "expired" | "error" | "disconnected";
  account: string | null;
  last_synced_at: string | null;
  last_error: string;
  scopes: string[];
}

export interface GitHubSyncResult {
  started_at: string;
  completed_at?: string;
  user: string;
  repositories: number;
  commits: number;
  pull_requests: number;
  issues: number;
  releases: number;
  errors: string[];
  status: "success" | "error";
}

export interface DailyPlan {
  id: string;
  date: string;
  priorities: Record<string, unknown>[];
  important_alerts: string[];
  upcoming_deadlines: Record<string, unknown>[];
  recommended_focus: string;
  potential_blockers: Record<string, unknown>[];
  tasks: string[];
  time_blocks: Record<string, unknown>[];
  completed_tasks: string[];
  incomplete_tasks: string[];
  evening_insights: string;
  tomorrow_priorities: Record<string, unknown>[];
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

// ── Intelligence API ──────────────────────────────────────────────────────
export const intelligence = {
  // Profile
  profile: () => api<UserProfile>("/api/intelligence/profile/me/"),
  updateProfile: (data: Partial<UserProfile>) =>
    api<UserProfile>("/api/intelligence/profile/me/", { method: "PATCH", body: JSON.stringify(data) }),

  // Data Sources
  dataSources: () => api<{ results: DataSource[] }>("/api/intelligence/data-sources/"),

  // Insights
  insights: (params?: { status?: string; type?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.type) query.set("type", params.type);
    return api<{ results: Insight[] }>(`/api/intelligence/insights/${query.toString() ? `?${query}` : ""}`);
  },
  markInsightHelpful: (id: string, helpful: boolean) =>
    api<{ status: string }>(`/api/intelligence/insights/${id}/mark_helpful/`, {
      method: "POST",
      body: JSON.stringify({ helpful }),
    }),
  dismissInsight: (id: string) =>
    api<{ status: string }>(`/api/intelligence/insights/${id}/dismiss/`, { method: "POST" }),

  // Alerts
  alerts: (params?: { status?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    return api<{ results: Alert[] }>(`/api/intelligence/alerts/${query.toString() ? `?${query}` : ""}`);
  },
  markAlertRead: (id: string) =>
    api<{ status: string }>(`/api/intelligence/alerts/${id}/mark_read/`, { method: "POST" }),
  resolveAlert: (id: string) =>
    api<{ status: string }>(`/api/intelligence/alerts/${id}/resolve/`, { method: "POST" }),

  // Daily Plan
  dailyPlan: () => api<DailyPlan>("/api/intelligence/daily-plans/today/"),

  // Integrations
  integrations: () => api<{ results: IntegrationConnection[] }>("/api/intelligence/integrations/"),
};

// ── GitHub OAuth API ──────────────────────────────────────────────────────
export const githubOAuth = {
  status: () => api<GitHubOAuthStatus>("/api/github/oauth/status/"),

  initiate: (redirectUri: string) =>
    api<{ authorization_url: string; state: string }>("/api/github/oauth/initiate/", {
      method: "POST",
      body: JSON.stringify({ redirect_uri: redirectUri }),
    }),

  callback: (code: string, state: string, redirectUri: string) =>
    api<{ success: boolean; connection: IntegrationConnection }>("/api/github/oauth/callback/", {
      method: "POST",
      body: JSON.stringify({ code, state, redirect_uri: redirectUri }),
    }),

  disconnect: () =>
    api<{ success: boolean; message: string }>("/api/github/oauth/disconnect/", { method: "POST" }),

  syncNow: () => api<GitHubSyncResult>("/api/github/sync/now/", { method: "POST" }),

  syncStatus: () =>
    api<{
      state: "connected" | "syncing" | "error" | "not_configured";
      last_synced_at: string | null;
      last_error: string;
      sync_frequency_hours: number;
    }>("/api/github/sync/status/"),
};
