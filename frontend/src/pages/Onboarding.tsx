import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BrainCircuit,
  Check,
  ChevronRight,
  Github,
  Globe,
  Linkedin,
  Instagram,
  Facebook,
  Twitter,
  User,
  Target,
  Clock,
  CheckCircle,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useProfile, useUpdateProfile, useGitHubStatus } from "@/hooks/useIntelligence";
import { githubOAuth } from "@/services/intelligence";
import type { UserProfile } from "@/services/intelligence";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

const STEPS = [
  { id: 1, label: "Profile", icon: User },
  { id: 2, label: "GitHub", icon: Github },
  { id: 3, label: "Website", icon: Globe },
  { id: 4, label: "LinkedIn", icon: Linkedin },
  { id: 5, label: "Instagram", icon: Instagram },
  { id: 6, label: "Facebook", icon: Facebook },
  { id: 7, label: "Twitter/X", icon: Twitter },
  { id: 8, label: "Goals", icon: Target },
  { id: 9, label: "Preferences", icon: Clock },
  { id: 10, label: "Done", icon: CheckCircle },
];

const GOAL_OPTIONS = [
  "Career growth",
  "Job search",
  "Portfolio improvement",
  "GitHub improvement",
  "Content creation",
  "Project development",
  "Learning",
  "Other",
];

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: profile, isLoading: profileLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const { data: githubStatus } = useGitHubStatus();
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [connectingGitHub, setConnectingGitHub] = useState(false);
  const [githubError, setGitHubError] = useState<string | null>(null);

  // Local form state
  const [form, setForm] = useState<Partial<UserProfile>>({});

  function patch(updates: Partial<UserProfile>) {
    setForm((prev) => ({ ...prev, ...updates }));
  }

  async function saveAndNext() {
    setSaving(true);
    try {
      await updateProfile.mutateAsync(form);
      setStep((s) => s + 1);
    } catch (e) {
      // error surfaced via updateProfile.error
    } finally {
      setSaving(false);
    }
  }

  async function handleConnectGitHub() {
    setConnectingGitHub(true);
    setGitHubError(null);
    try {
      const redirectUri = `${window.location.origin}/onboarding`;
      const { authorization_url } = await githubOAuth.initiate(redirectUri);
      window.location.href = authorization_url;
    } catch (e) {
      setGitHubError(e instanceof Error ? e.message : "Failed to initiate GitHub connection");
      setConnectingGitHub(false);
    }
  }

  async function finishOnboarding() {
    setSaving(true);
    try {
      await updateProfile.mutateAsync({ ...form, onboarding_completed: true });
      navigate("/");
    } catch {
      setSaving(false);
    }
  }

  // Derived values
  const githubConnected = githubStatus?.connected ?? false;
  const displayName = form.professional_title ?? profile?.professional_title ?? "";
  const displayUsername = profile?.username ?? user?.username ?? "";

  if (profileLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#6366f1] to-[#22d3ee]">
          <BrainCircuit className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold">Personalized AI Agent</p>
          <p className="text-[10px] text-muted">Setup</p>
        </div>
        <div className="ml-auto">
          <p className="text-xs text-muted">
            Step {step} of {STEPS.length}
          </p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1 w-full bg-border">
        <div
          className="h-1 bg-gradient-to-r from-[#6366f1] to-[#22d3ee] transition-all duration-500"
          style={{ width: `${(step / STEPS.length) * 100}%` }}
        />
      </div>

      {/* Step indicator */}
      <div className="scrollbar-none overflow-x-auto border-b border-border">
        <div className="flex min-w-max items-center gap-1 px-4 py-3">
          {STEPS.map((s) => {
            const Icon = s.icon;
            const done = step > s.id;
            const active = step === s.id;
            return (
              <div key={s.id} className="flex items-center">
                <div
                  className={cn(
                    "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors",
                    active && "bg-primary/15 text-primary",
                    done && "text-green-500",
                    !active && !done && "text-muted"
                  )}
                >
                  {done ? <Check className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
                  {s.label}
                </div>
                {s.id < STEPS.length && <ChevronRight className="mx-1 h-3 w-3 text-border" />}
              </div>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto w-full max-w-xl flex-1 px-6 py-8">
        {/* Step 1 — Personal Profile */}
        {step === 1 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold">Tell us about yourself</h2>
              <p className="mt-1 text-sm text-muted">
                This helps personalise your AI agent's recommendations.
              </p>
            </div>

            <div className="space-y-4">
              <Field label="Name" hint="Your display name">
                <Input
                  placeholder="Your name"
                  defaultValue={profile?.username ?? user?.username ?? ""}
                  readOnly
                  className="bg-muted/5 text-muted"
                />
                <p className="mt-1 text-[11px] text-muted">From your account — cannot be changed here.</p>
              </Field>

              <Field label="Email" hint="Your email address">
                <Input
                  placeholder="Email"
                  defaultValue={profile?.email ?? user?.email ?? ""}
                  readOnly
                  className="bg-muted/5 text-muted"
                />
                <p className="mt-1 text-[11px] text-muted">From your account — cannot be changed here.</p>
              </Field>

              <Field label="Professional title / role" hint="e.g. Senior Software Engineer">
                <Input
                  placeholder="e.g. Senior Software Engineer"
                  defaultValue={profile?.professional_title ?? ""}
                  onChange={(e) => patch({ professional_title: e.target.value })}
                />
              </Field>

              <Field label="Short bio" hint="A few words about you (optional)">
                <textarea
                  className="w-full rounded-md border border-border bg-card-solid/50 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/40 resize-none"
                  rows={3}
                  placeholder="e.g. Full-stack developer focused on TypeScript and Python."
                  defaultValue={profile?.bio ?? ""}
                  onChange={(e) => patch({ bio: e.target.value })}
                />
              </Field>

              <Field label="Timezone" hint="Your local timezone (optional)">
                <Input
                  placeholder="e.g. America/New_York"
                  defaultValue={profile?.timezone ?? ""}
                  onChange={(e) => patch({ timezone: e.target.value })}
                />
              </Field>
            </div>

            {updateProfile.isError && (
              <ErrorBanner message={updateProfile.error?.message} />
            )}

            <StepActions onNext={saveAndNext} saving={saving} />
          </div>
        )}

        {/* Step 2 — GitHub */}
        {step === 2 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold">Connect GitHub</h2>
              <p className="mt-1 text-sm text-muted">
                Analyse your repositories, commits, and development patterns.
              </p>
            </div>

            {githubConnected ? (
              <div className="rounded-xl border border-green-500/30 bg-green-500/5 p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <p className="font-medium text-green-500">GitHub Connected</p>
                </div>
                <p className="text-sm text-muted">
                  Connected as <strong>{githubStatus?.account}</strong>
                </p>
                {githubStatus?.last_synced_at && (
                  <p className="text-xs text-muted">
                    Last synced: {new Date(githubStatus.last_synced_at).toLocaleString()}
                  </p>
                )}
                <div className="pt-1">
                  <Badge variant="success">Connected</Badge>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-card-solid/30 p-6 text-center space-y-4">
                <Github className="mx-auto h-10 w-10 text-muted" />
                <div>
                  <p className="font-medium">Not connected</p>
                  <p className="mt-1 text-sm text-muted">
                    Connect to get GitHub-based insights and recommendations.
                  </p>
                </div>
                {githubError && <ErrorBanner message={githubError} />}
                <div className="flex justify-center gap-3">
                  <Button
                    variant="gradient"
                    onClick={handleConnectGitHub}
                    disabled={connectingGitHub}
                  >
                    {connectingGitHub ? (
                      <><Loader2 className="h-4 w-4 animate-spin" /> Connecting...</>
                    ) : (
                      <><Github className="h-4 w-4" /> Connect GitHub</>
                    )}
                  </Button>
                  <Button variant="ghost" onClick={() => setStep((s) => s + 1)}>
                    Skip for now
                  </Button>
                </div>
                <p className="text-[11px] text-muted">
                  You can always connect later from the GitHub integration page.
                </p>
              </div>
            )}

            <StepActions
              onNext={() => setStep((s) => s + 1)}
              saving={false}
              nextLabel={githubConnected ? "Continue" : "Skip"}
            />
          </div>
        )}

        {/* Step 3 — Portfolio / Website */}
        {step === 3 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold">Portfolio / Website</h2>
              <p className="mt-1 text-sm text-muted">
                Enter your website or portfolio URL.
              </p>
            </div>

            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-600 dark:text-amber-400">
              <strong>Note:</strong> Entering a URL saves it as a profile link. It does not mean the
              site has been analysed. Analysis requires separate backend processing.
            </div>

            <Field label="Website / Portfolio URL">
              <Input
                placeholder="https://yourwebsite.com"
                type="url"
                defaultValue={profile?.portfolio_url ?? ""}
                onChange={(e) => patch({ portfolio_url: e.target.value })}
              />
            </Field>

            <div className="rounded-lg border border-border p-3 text-xs text-muted space-y-1">
              <p className="font-medium text-foreground">Status: Profile URL only</p>
              <p>This URL will be saved to your profile. It has not been connected or verified.</p>
            </div>

            {updateProfile.isError && <ErrorBanner message={updateProfile.error?.message} />}
            <StepActions onNext={saveAndNext} saving={saving} nextLabel="Save & Continue" />
          </div>
        )}

        {/* Step 4 — LinkedIn */}
        {step === 4 && (
          <SocialStep
            step={step}
            title="LinkedIn"
            icon={<Linkedin className="h-5 w-5" />}
            description="Add your LinkedIn profile URL."
            placeholder="https://linkedin.com/in/yourname"
            field="linkedin_url"
            defaultValue={profile?.linkedin_url ?? ""}
            note="LinkedIn data is not automatically imported. This saves your profile link only."
            onPatch={patch}
            onNext={saveAndNext}
            saving={saving}
            error={updateProfile.error?.message}
          />
        )}

        {/* Step 5 — Instagram */}
        {step === 5 && (
          <SocialStep
            step={step}
            title="Instagram"
            icon={<Instagram className="h-5 w-5" />}
            description="Add your Instagram profile URL."
            placeholder="https://instagram.com/yourname"
            field="instagram_url"
            defaultValue={profile?.instagram_url ?? ""}
            note="Instagram is not connected. This saves your profile link only."
            onPatch={patch}
            onNext={saveAndNext}
            saving={saving}
            error={updateProfile.error?.message}
          />
        )}

        {/* Step 6 — Facebook */}
        {step === 6 && (
          <SocialStep
            step={step}
            title="Facebook"
            icon={<Facebook className="h-5 w-5" />}
            description="Add your Facebook profile URL."
            placeholder="https://facebook.com/yourname"
            field="facebook_url"
            defaultValue={profile?.facebook_url ?? ""}
            note="Facebook is not connected. This saves your profile link only."
            onPatch={patch}
            onNext={saveAndNext}
            saving={saving}
            error={updateProfile.error?.message}
          />
        )}

        {/* Step 7 — Twitter/X */}
        {step === 7 && (
          <SocialStep
            step={step}
            title="Twitter / X"
            icon={<Twitter className="h-5 w-5" />}
            description="Add your Twitter/X profile URL."
            placeholder="https://x.com/yourname"
            field="twitter_url"
            defaultValue={profile?.twitter_url ?? ""}
            note="Twitter/X is not connected. This saves your profile link only."
            onPatch={patch}
            onNext={saveAndNext}
            saving={saving}
            error={updateProfile.error?.message}
          />
        )}

        {/* Step 8 — Goals */}
        {step === 8 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold">Your Goals</h2>
              <p className="mt-1 text-sm text-muted">
                Select the goals most relevant to you. These shape the intelligence recommendations.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {GOAL_OPTIONS.map((goal) => {
                const current = form.primary_goals ?? profile?.primary_goals ?? [];
                const selected = current.includes(goal);
                return (
                  <button
                    key={goal}
                    onClick={() => {
                      const updated = selected
                        ? current.filter((g) => g !== goal)
                        : [...current, goal];
                      patch({ primary_goals: updated });
                    }}
                    className={cn(
                      "flex items-center gap-2 rounded-lg border p-3 text-sm text-left transition-colors",
                      selected
                        ? "border-primary/60 bg-primary/10 text-primary"
                        : "border-border hover:border-primary/30 hover:bg-muted/5"
                    )}
                  >
                    {selected && <Check className="h-3.5 w-3.5 flex-shrink-0" />}
                    {!selected && <div className="h-3.5 w-3.5 flex-shrink-0" />}
                    {goal}
                  </button>
                );
              })}
            </div>

            {updateProfile.isError && <ErrorBanner message={updateProfile.error?.message} />}
            <StepActions onNext={saveAndNext} saving={saving} nextLabel="Save & Continue" />
          </div>
        )}

        {/* Step 9 — Working Preferences */}
        {step === 9 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold">Working Preferences</h2>
              <p className="mt-1 text-sm text-muted">
                Help your AI agent understand when you work.
              </p>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Field label="Work day start time">
                  <Input
                    type="time"
                    defaultValue={profile?.working_hours_start ?? "09:00"}
                    onChange={(e) => patch({ working_hours_start: e.target.value })}
                  />
                </Field>
                <Field label="Work day end time">
                  <Input
                    type="time"
                    defaultValue={profile?.working_hours_end ?? "18:00"}
                    onChange={(e) => patch({ working_hours_end: e.target.value })}
                  />
                </Field>
              </div>

              <Field label="Working days">
                <div className="flex flex-wrap gap-2">
                  {DAYS.map((day, idx) => {
                    // backend uses 0=Monday … 6=Sunday
                    const current = form.working_days ?? profile?.working_days ?? [0, 1, 2, 3, 4];
                    const selected = current.includes(idx);
                    return (
                      <button
                        key={day}
                        onClick={() => {
                          const updated = selected
                            ? current.filter((d) => d !== idx)
                            : [...current, idx];
                          patch({ working_days: updated });
                        }}
                        className={cn(
                          "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                          selected
                            ? "border-primary/60 bg-primary/10 text-primary"
                            : "border-border text-muted hover:border-primary/30"
                        )}
                      >
                        {day.slice(0, 3)}
                      </button>
                    );
                  })}
                </div>
              </Field>

              <Field label="Timezone">
                <Input
                  placeholder="e.g. America/New_York"
                  defaultValue={form.timezone ?? profile?.timezone ?? ""}
                  onChange={(e) => patch({ timezone: e.target.value })}
                />
              </Field>
            </div>

            {updateProfile.isError && <ErrorBanner message={updateProfile.error?.message} />}
            <StepActions onNext={saveAndNext} saving={saving} nextLabel="Save & Continue" />
          </div>
        )}

        {/* Step 10 — Completion */}
        {step === 10 && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-500/10">
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
              <h2 className="text-2xl font-semibold">You're all set!</h2>
              <p className="mt-2 text-sm text-muted">
                Here's a summary of what you've configured:
              </p>
            </div>

            <div className="space-y-3">
              <SourceSummaryRow
                label="Profile"
                status="connected"
                detail={`${displayUsername}${displayName ? ` — ${displayName}` : ""}`}
              />
              <SourceSummaryRow
                label="GitHub"
                status={githubConnected ? "connected" : "not_connected"}
                detail={
                  githubConnected
                    ? `Connected as ${githubStatus?.account}`
                    : "Not connected — connect later from Integrations"
                }
              />
              <SourceSummaryRow
                label="Website"
                status={form.portfolio_url || profile?.portfolio_url ? "user_provided" : "not_connected"}
                detail={form.portfolio_url || profile?.portfolio_url || "Not provided"}
              />
              <SourceSummaryRow
                label="LinkedIn"
                status={form.linkedin_url || profile?.linkedin_url ? "user_provided" : "not_connected"}
                detail={form.linkedin_url || profile?.linkedin_url || "Not provided"}
              />
              <SourceSummaryRow
                label="Instagram"
                status={form.instagram_url || profile?.instagram_url ? "user_provided" : "not_connected"}
                detail={form.instagram_url || profile?.instagram_url || "Not provided"}
              />
              <SourceSummaryRow
                label="Facebook"
                status={form.facebook_url || profile?.facebook_url ? "user_provided" : "not_connected"}
                detail={form.facebook_url || profile?.facebook_url || "Not provided"}
              />
              <SourceSummaryRow
                label="Twitter/X"
                status={form.twitter_url || profile?.twitter_url ? "user_provided" : "not_connected"}
                detail={form.twitter_url || profile?.twitter_url || "Not provided"}
              />
              <SourceSummaryRow
                label="Goals"
                status={(form.primary_goals ?? profile?.primary_goals ?? []).length > 0 ? "connected" : "not_connected"}
                detail={
                  (form.primary_goals ?? profile?.primary_goals ?? []).length > 0
                    ? (form.primary_goals ?? profile?.primary_goals ?? []).join(", ")
                    : "None selected"
                }
              />
            </div>

            <div className="rounded-lg border border-border bg-muted/5 p-3 text-xs text-muted space-y-1">
              <p className="font-medium text-foreground">Status Key</p>
              <div className="flex flex-wrap gap-3">
                <span><span className="text-green-500">●</span> Connected — live data source</span>
                <span><span className="text-blue-500">●</span> User Provided — profile link only</span>
                <span><span className="text-muted">●</span> Not Connected</span>
              </div>
            </div>

            <Button
              variant="gradient"
              className="w-full"
              onClick={finishOnboarding}
              disabled={saving}
            >
              {saving ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Saving...</>
              ) : (
                "Go to Dashboard"
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{label}</label>
      {hint && <p className="text-xs text-muted">{hint}</p>}
      {children}
    </div>
  );
}

function ErrorBanner({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-2 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-500">
      <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
      {message}
    </div>
  );
}

function StepActions({
  onNext,
  saving,
  nextLabel = "Continue",
}: {
  onNext: () => void;
  saving: boolean;
  nextLabel?: string;
}) {
  return (
    <div className="flex justify-end pt-2">
      <Button variant="gradient" onClick={onNext} disabled={saving}>
        {saving ? (
          <><Loader2 className="h-4 w-4 animate-spin" /> Saving...</>
        ) : (
          <>{nextLabel} <ChevronRight className="h-4 w-4" /></>
        )}
      </Button>
    </div>
  );
}

function SocialStep({
  title,
  icon,
  description,
  placeholder,
  field,
  defaultValue,
  note,
  onPatch,
  onNext,
  saving,
  error,
}: {
  step: number;
  title: string;
  icon: React.ReactNode;
  description: string;
  placeholder: string;
  field: keyof UserProfile;
  defaultValue: string;
  note: string;
  onPatch: (u: Partial<UserProfile>) => void;
  onNext: () => void;
  saving: boolean;
  error?: string;
}) {
  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-2">
          {icon}
          <h2 className="text-xl font-semibold">{title}</h2>
        </div>
        <p className="mt-1 text-sm text-muted">{description}</p>
      </div>

      <Field label={`${title} URL`}>
        <Input
          placeholder={placeholder}
          type="url"
          defaultValue={defaultValue}
          onChange={(e) => onPatch({ [field]: e.target.value } as Partial<UserProfile>)}
        />
      </Field>

      <div className="rounded-lg border border-border p-3 text-xs text-muted space-y-1">
        <p className="font-medium text-foreground">Status: Profile URL only</p>
        <p>{note}</p>
      </div>

      {error && <ErrorBanner message={error} />}
      <StepActions onNext={onNext} saving={saving} nextLabel="Save & Continue" />
    </div>
  );
}

type SourceStatus = "connected" | "user_provided" | "not_connected" | "pending" | "error";

function SourceSummaryRow({
  label,
  status,
  detail,
}: {
  label: string;
  status: SourceStatus;
  detail: string;
}) {
  // colours kept for future use
  void ({ connected: "text-green-500", user_provided: "text-blue-500", not_connected: "text-muted", pending: "text-amber-500", error: "text-red-500" });

  const labels: Record<SourceStatus, string> = {
    connected: "Connected",
    user_provided: "Profile URL",
    not_connected: "Not Connected",
    pending: "Pending",
    error: "Error",
  };

  return (
    <div className="flex items-start justify-between gap-3 rounded-lg border border-border p-3 text-sm">
      <div className="flex-1 min-w-0">
        <p className="font-medium">{label}</p>
        <p className="truncate text-xs text-muted">{detail}</p>
      </div>
      <Badge
        variant={status === "connected" ? "success" : status === "user_provided" ? "info" : "default"}
        className="flex-shrink-0"
      >
        {labels[status]}
      </Badge>
    </div>
  );
}
