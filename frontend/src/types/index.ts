/** Shared API response types (mirror the Django DRF serializers). */

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: "owner" | "admin" | "viewer";
  github_username: string;
  avatar_url: string;
  bio: string;
  date_joined: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  user: User;
}

export interface Repository {
  id: string;
  name: string;
  full_name: string;
  description: string;
  language: string;
  url: string;
  stars: number;
  forks: number;
  open_issues: number;
  open_prs: number;
  last_commit_at: string | null;
  last_commit_days: number | null;
  status: "active" | "at_risk" | "inactive";
  health: string;
}

export interface Commit {
  id: string;
  repository: string;
  sha: string;
  author: string;
  message: string;
  date: string;
  additions: number;
  deletions: number;
  changed_files: number;
}

export interface GithubAnalytics {
  period_start: string;
  period_end: string;
  totals: { commits: number; additions: number; prs_merged: number; issues_closed: number; active_repos: number };
  productivity_score: number;
  daily: { date: string; commits: number; additions: number; prs_merged: number; issues_closed: number; productivity_score: number; coding_hours: number }[];
  repos: {
    name: string;
    language: string;
    commits: number;
    additions: number;
    prs_merged: number;
    status: string;
    last_commit_days: number | null;
  }[];
  insights?: string[];
}

export interface ContributionPoint {
  date: string;
  commits: number;
}

export interface GithubInsight {
  id: string;
  repository: string | null;
  kind: string;
  severity: "info" | "warning" | "critical";
  text: string;
  created_at: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: "todo" | "in_progress" | "done" | "blocked";
  priority: "low" | "medium" | "high" | "urgent";
  due_date: string | null;
  estimated_hours: number;
  completed_at: string | null;
  project: string | null;
  project_name: string | null;
  created_at: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  location: string;
  url: string;
}

export interface Briefing {
  id: string;
  kind: "morning" | "eod";
  date: string;
  content: string;
  data: Record<string, unknown>;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  client: string;
  description: string;
  status: string;
  start_date: string | null;
  end_date: string | null;
  backend_pct: number;
  frontend_pct: number;
  testing_pct: number;
  deployment_pct: number;
  pending_bugs: number;
  completion_pct: number;
  risk_score: number;
  velocity: number;
  delivery: { predicted_delivery: string | null; confidence: number | null };
  burndown: { date: string; remaining: number; total_pct: number }[];
}

export interface Report {
  id: string;
  period: string;
  title: string;
  period_start: string;
  period_end: string;
  content: string;
  html: string;
  data: Record<string, unknown>;
  generated_by: string;
  created_at: string;
}

export interface ResumeVersion {
  id: string;
  version_number: number;
  full_name: string;
  title: string;
  summary: string;
  contact: Record<string, string>;
  experience: unknown[];
  projects: unknown[];
  education: unknown[];
  skills: string[];
  ats_score: number;
  keywords_missing: string[];
  content: string;
  created_at: string;
}

export interface PortfolioProject {
  id: string;
  name: string;
  description: string;
  repository: string | null;
  skills: string[];
  screenshots: string[];
  readme: string;
  deployment_status: string;
  live_url: string;
  last_release_tag: string;
  updated_at: string;
}

export interface LearningItem {
  id: string;
  kind: string;
  title: string;
  url: string;
  reason: string;
  priority: string;
  completed: boolean;
  created_at: string;
}

export interface LearningSuggestion {
  id: string;
  date: string;
  kind: string;
  title: string;
  reason: string;
  source: string;
  created_at: string;
}

export interface LearningRoadmap {
  id: string;
  title: string;
  level: string;
  items: { topic: string; resource: string; why: string }[];
  created_at: string;
}

export interface LinkedInProfile {
  id: string;
  headline: string;
  about: string;
  location: string;
  experience: unknown[];
  skills: string[];
  education: unknown[];
  certifications: unknown[];
  updated_at: string;
}

export interface LinkedInScore {
  score: number;
  breakdown: Record<string, number>;
  suggestions: string[];
  best_times?: { window: string; reason: string }[];
}

export interface PostIdea {
  id: string;
  topic: string;
  content: string;
  hashtags: string[];
  source: string;
  created_at: string;
}

export interface Notification {
  id: string;
  kind: string;
  title: string;
  body: string;
  severity: string;
  link: string;
  read: boolean;
  created_at: string;
}

export interface Overview {
  commits_week: number;
  productivity_score: number;
  active_repos: number;
  tasks_pending: number;
  projects: number;
  project_avg_completion: number;
  projects_at_risk: number;
  linkedin_score: number | null;
  resume_ats: number | null;
  learning_open: number;
}

export interface CommandResult {
  intent: string;
  agent: string;
  matched: boolean;
  message: string;
  data: Record<string, unknown>;
}
