import { useState } from "react";
import {
  Bot,
  Globe,
  UserRound,
  Github,
  Linkedin,
  Instagram,
  Facebook,
  Twitter,
  Cpu,
  KeyRound,
  Moon,
  Sun,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { useProviders } from "@/hooks";
import { useProfile, useUpdateProfile, useGitHubStatus, useIntegrations } from "@/hooks/useIntelligence";
import { normalizeStatus, statusLabel, statusTone } from "@/lib/status";
import { cn } from "@/lib/utils";

export default function Profile() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const { data: providers } = useProviders();
  const { data: profile, isLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const { data: githubStatus } = useGitHubStatus();
  const { data: integrationsData } = useIntegrations();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const integrations = integrationsData?.results ?? [];

  function startEdit() {
    setForm({
      professional_title: profile?.professional_title ?? "",
      bio: profile?.bio ?? "",
      portfolio_url: profile?.portfolio_url ?? "",
      github_url: profile?.github_url ?? "",
      linkedin_url: profile?.linkedin_url ?? "",
      instagram_url: profile?.instagram_url ?? "",
      facebook_url: profile?.facebook_url ?? "",
      twitter_url: profile?.twitter_url ?? "",
      timezone: profile?.timezone ?? "",
    });
    setEditing(true);
  }

  async function saveEdit() {
    setSaving(true);
    try {
      await updateProfile.mutateAsync(form);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  const githubOAuthConnected = githubStatus?.connected ?? false;
  // githubIntegration: reserved for future per-integration actions
  void integrations.find((i) => i.platform === "github");

  return (
    <div>
      <PageHeader
        title="Profile & Settings"
        description="Your profile information, integrations, and preferences."
        action={
          !editing ? (
            <Button variant="outline" size="sm" onClick={startEdit}>
              Edit Profile
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
                Cancel
              </Button>
              <Button variant="gradient" size="sm" onClick={saveEdit} disabled={saving}>
                {saving ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Saving...</>
                ) : (
                  "Save"
                )}
              </Button>
            </div>
          )
        }
      />

      {updateProfile.isError && (
        <div className="mb-4 flex items-start gap-2 rounded-xl border border-red-500/30 bg-red-500/5 p-3 text-sm text-red-500">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          {updateProfile.error?.message}
        </div>
      )}

      {updateProfile.isSuccess && !editing && (
        <div className="mb-4 flex items-start gap-2 rounded-xl border border-green-500/30 bg-green-500/5 p-3 text-sm text-green-500">
          <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          Profile saved successfully.
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Account info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <UserRound className="h-4 w-4" /> Account
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Username" value={user?.username ?? "—"} />
            <Row label="Email" value={user?.email ?? "—"} />
            {user?.role && <Row label="Role" value={<Badge variant="primary">{user.role}</Badge>} />}
            {isLoading ? (
              <Row label="Professional title" value="Loading..." />
            ) : editing ? (
              <div className="space-y-1">
                <label className="text-xs text-muted">Professional title</label>
                <Input
                  value={form.professional_title ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, professional_title: e.target.value }))}
                  placeholder="e.g. Senior Software Engineer"
                />
              </div>
            ) : (
              <Row label="Professional title" value={profile?.professional_title || <span className="text-muted">—</span>} />
            )}
            {editing ? (
              <div className="space-y-1">
                <label className="text-xs text-muted">Bio</label>
                <textarea
                  className="w-full rounded-md border border-border bg-card-solid/50 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/40 resize-none"
                  rows={3}
                  value={form.bio ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
                  placeholder="A few words about you..."
                />
              </div>
            ) : (
              profile?.bio && <Row label="Bio" value={profile.bio} />
            )}
            {editing ? (
              <div className="space-y-1">
                <label className="text-xs text-muted">Timezone</label>
                <Input
                  value={form.timezone ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))}
                  placeholder="e.g. America/New_York"
                />
              </div>
            ) : (
              <Row label="Timezone" value={profile?.timezone || <span className="text-muted">—</span>} />
            )}
            {(profile?.primary_goals?.length ?? 0) > 0 && (
              <div>
                <p className="mb-1 text-muted">Goals</p>
                <div className="flex flex-wrap gap-1">
                  {(profile?.primary_goals ?? []).map((g) => (
                    <Badge key={g} variant="info">{g}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Connected Integrations — clearly separated from profile links */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <CheckCircle className="h-4 w-4" /> Connected Integrations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p className="text-xs text-muted">
              These are authenticated connections where the app can read your data.
              Different from profile links below.
            </p>

            {/* GitHub OAuth connection */}
            <div className={cn(
              "flex items-center justify-between rounded-lg border p-3",
              githubOAuthConnected ? "border-green-500/30 bg-green-500/5" : "border-border"
            )}>
              <div className="flex items-center gap-2">
                <Github className="h-4 w-4" />
                <div>
                  <p className="font-medium">GitHub</p>
                  {githubOAuthConnected && githubStatus?.account && (
                    <p className="text-xs text-muted">@{githubStatus.account}</p>
                  )}
                </div>
              </div>
              <Badge variant={githubOAuthConnected ? "success" : "default"}>
                {githubOAuthConnected ? "Connected" : "Not Connected"}
              </Badge>
            </div>

            {/* Other integrations */}
            {integrations
              .filter((i) => i.platform !== "github")
              .map((conn) => {
                const tone = statusTone(conn.status);
                const connected = normalizeStatus(conn.status) === "connected";
                return (
                  <div
                    key={conn.id}
                    className={cn(
                      "flex items-center justify-between rounded-lg border p-3",
                      connected ? "border-green-500/30 bg-green-500/5" : "border-border"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <Globe className="h-4 w-4" />
                      <p className="font-medium capitalize">{conn.platform}</p>
                    </div>
                    <Badge variant={tone}>{statusLabel(conn.status)}</Badge>
                  </div>
                );
              })}

            {integrations.length === 0 && !githubOAuthConnected && (
              <p className="text-sm text-muted">No authenticated integrations yet.</p>
            )}
          </CardContent>
        </Card>

        {/* Profile Links — clearly labeled as links, NOT connections */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <Globe className="h-4 w-4" /> Profile Links
              <Badge variant="info" className="ml-1">Links only — not connected</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-xs text-muted">
              These are URLs you've added to your profile. They are stored as links only —
              they are <strong>not</strong> authenticated integrations and data is not automatically imported.
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <ProfileLinkField
                icon={<Globe className="h-4 w-4" />}
                label="Website / Portfolio"
                field="portfolio_url"
                value={editing ? form.portfolio_url : profile?.portfolio_url}
                editing={editing}
                onEdit={(v) => setForm((f) => ({ ...f, portfolio_url: v }))}
                placeholder="https://yourwebsite.com"
              />
              <ProfileLinkField
                icon={<Github className="h-4 w-4" />}
                label="GitHub URL"
                field="github_url"
                value={editing ? form.github_url : profile?.github_url}
                editing={editing}
                onEdit={(v) => setForm((f) => ({ ...f, github_url: v }))}
                placeholder="https://github.com/yourname"
                warning={
                  githubOAuthConnected
                    ? undefined
                    : "This is a profile URL only. Use Integrations to connect GitHub."
                }
              />
              <ProfileLinkField
                icon={<Linkedin className="h-4 w-4" />}
                label="LinkedIn URL"
                field="linkedin_url"
                value={editing ? form.linkedin_url : profile?.linkedin_url}
                editing={editing}
                onEdit={(v) => setForm((f) => ({ ...f, linkedin_url: v }))}
                placeholder="https://linkedin.com/in/yourname"
              />
              <ProfileLinkField
                icon={<Instagram className="h-4 w-4" />}
                label="Instagram URL"
                field="instagram_url"
                value={editing ? form.instagram_url : profile?.instagram_url}
                editing={editing}
                onEdit={(v) => setForm((f) => ({ ...f, instagram_url: v }))}
                placeholder="https://instagram.com/yourname"
              />
              <ProfileLinkField
                icon={<Facebook className="h-4 w-4" />}
                label="Facebook URL"
                field="facebook_url"
                value={editing ? form.facebook_url : profile?.facebook_url}
                editing={editing}
                onEdit={(v) => setForm((f) => ({ ...f, facebook_url: v }))}
                placeholder="https://facebook.com/yourname"
              />
              <ProfileLinkField
                icon={<Twitter className="h-4 w-4" />}
                label="Twitter / X URL"
                field="twitter_url"
                value={editing ? form.twitter_url : profile?.twitter_url}
                editing={editing}
                onEdit={(v) => setForm((f) => ({ ...f, twitter_url: v }))}
                placeholder="https://x.com/yourname"
              />
            </div>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-sm">
              {theme === "dark" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />} Appearance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Dark mode</p>
                <p className="text-xs text-muted">Themes sync across the whole dashboard.</p>
              </div>
              <Switch
                checked={theme === "dark"}
                onCheckedChange={(on) => setTheme(on ? "dark" : "light")}
              />
            </div>
          </CardContent>
        </Card>

        {/* AI providers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <Cpu className="h-4 w-4" /> AI Providers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {(providers?.providers ?? []).map((p) => (
                <div
                  key={p.name}
                  className={cn(
                    "flex items-center justify-between rounded-lg border p-3",
                    p.active && "border-primary/50 bg-primary/5"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Bot className="h-4 w-4 text-muted" />
                    <span className="text-sm font-medium capitalize">{p.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={p.active ? "primary" : "default"}>{p.active ? "active" : "inactive"}</Badge>
                    <Badge variant={p.available ? "success" : "warning"}>{p.available ? "available" : "unconfigured"}</Badge>
                  </div>
                </div>
              ))}
              {(!providers?.providers || providers.providers.length === 0) && (
                <p className="text-sm text-muted">No providers configured.</p>
              )}
            </div>
            <p className="mt-3 flex items-center gap-1.5 text-xs text-muted">
              <KeyRound className="h-3.5 w-3.5" />
              Keys live in the backend environment, never the browser. Set{" "}
              <code className="font-mono text-[11px]">AI_PROVIDER</code> and restart.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span className="text-muted">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}

function ProfileLinkField({
  icon,
  label,
  value,
  editing,
  onEdit,
  placeholder,
  warning,
}: {
  icon: React.ReactNode;
  label: string;
  field: string;
  value?: string;
  editing: boolean;
  onEdit: (v: string) => void;
  placeholder: string;
  warning?: string;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-1.5 text-xs font-medium text-muted">
        {icon} {label}
      </div>
      {editing ? (
        <Input
          type="url"
          placeholder={placeholder}
          value={value ?? ""}
          onChange={(e) => onEdit(e.target.value)}
        />
      ) : (
        <div>
          {value ? (
            <a
              href={value}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline break-all"
            >
              {value}
            </a>
          ) : (
            <p className="text-sm text-muted">—</p>
          )}
        </div>
      )}
      {warning && !editing && (
        <p className="text-[11px] text-amber-500">{warning}</p>
      )}
      {!editing && value && (
        <Badge variant="default" className="text-[10px]">Profile URL only</Badge>
      )}
    </div>
  );
}
