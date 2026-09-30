import { useState } from "react";
import {
  Activity,
  AlertCircle,
  Bot,
  CheckCircle2,
  Cpu,
  EyeOff,
  Loader2,
  Plus,
  Server,
  Settings2,
  Trash2,
  Wifi,
  WifiOff,
  Zap,
} from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  useCreateProviderConnection,
  useDeleteProviderConnection,
  useDisableSkill,
  useEnableSkill,
  useProviderConnections,
  useSkillExecutions,
  useSkills,
  useSystemHealth,
  useTestProviderConnection,
  useTestSkill,
  useUpdateProviderConnection,
  useValidateSkill,
} from "@/hooks";
import type { ProviderConnection, ProviderConnectionFormData } from "@/types";
import { normalizeStatus, statusLabel, statusTone } from "@/lib/status";
import { cn } from "@/lib/utils";

// ── Helpers ──────────────────────────────────────────────────────────────
/**
 * Human labels for AI-provider error codes.
 *
 * Covers both surfaces: the `AI_PROVIDER_*` codes returned by connection
 * tests/diagnostics, and the lowercase snake_case codes persisted on
 * connections (`auth_failed`, `rate_limited`, …). Lookup is case-insensitive.
 */
const ERROR_LABELS: Record<string, string> = {
  // AI provider surface (AI_*)
  AI_PROVIDER_NOT_CONFIGURED: "Provider not configured",
  AI_PROVIDER_AUTH_FAILED: "Authentication failed",
  AI_PROVIDER_TIMEOUT: "Timeout",
  AI_PROVIDER_RATE_LIMITED: "Rate limited",
  AI_PROVIDER_UNAVAILABLE: "Provider unavailable",
  AI_MODEL_NOT_FOUND: "Model not found",
  AI_PROVIDER_UNKNOWN_ERROR: "Unknown provider error",
  // Persisted connection codes (lowercase snake_case)
  not_configured: "Not configured",
  auth_failed: "Authentication failed",
  invalid_credentials: "Invalid credentials",
  permission_denied: "Permission denied",
  rate_limited: "Rate limited",
  timeout: "Timeout",
  network_error: "Network error",
  connection_refused: "Connection refused",
  dns_error: "DNS error",
  tls_error: "TLS error",
  model_not_found: "Model not found",
  invalid_base_url: "Invalid base URL",
  api_error: "API error",
  service_unavailable: "Service unavailable",
  unknown_error: "Unknown error",
  // Legacy uppercase spellings
  INVALID_CREDENTIALS: "Invalid credentials",
  FORBIDDEN: "Forbidden",
  MODEL_NOT_FOUND: "Model not found",
  RATE_LIMITED: "Rate limited",
  TIMEOUT: "Timeout",
  DNS_ERROR: "DNS error",
  CONNECTION_REFUSED: "Connection refused",
  TLS_ERROR: "TLS error",
  INVALID_BASE_URL: "Invalid base URL",
  PROVIDER_UNAVAILABLE: "Provider unavailable",
  SERVER_ERROR: "Server error",
};

const normalizeErrorLabel = (code: string): string => {
  if (!code) return "";
  return ERROR_LABELS[code] ?? ERROR_LABELS[code.toLowerCase()] ?? code;
};

// ── Provider Form ─────────────────────────────────────────────────────────
interface ProviderFormProps {
  initial?: Partial<ProviderConnectionFormData & { id: string }>;
  onSave: (data: ProviderConnectionFormData) => Promise<void>;
  onCancel: () => void;
  isPending: boolean;
  error?: string;
}

function ProviderForm({ initial, onSave, onCancel, isPending, error }: ProviderFormProps) {
  const [form, setForm] = useState<ProviderConnectionFormData>({
    provider_id: initial?.provider_id ?? "",
    display_name: initial?.display_name ?? "",
    base_url: initial?.base_url ?? "",
    model: initial?.model ?? "",
    api_key: "",
    enabled: initial?.enabled ?? true,
    is_default: initial?.is_default ?? false,
  });
  const [showKey, setShowKey] = useState(false);

  const set = (k: keyof ProviderConnectionFormData, v: string | boolean) =>
    setForm((prev) => ({ ...prev, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave(form);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-muted">Provider ID</label>
          <Input
            required
            placeholder="openai / anthropic / ollama / custom"
            value={form.provider_id}
            onChange={(e) => set("provider_id", e.target.value)}
          />
        </div>
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-muted">Display name</label>
          <Input
            placeholder="My OpenAI key"
            value={form.display_name}
            onChange={(e) => set("display_name", e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted">Base URL (optional)</label>
          <Input
            placeholder="https://api.openai.com/v1"
            value={form.base_url}
            onChange={(e) => set("base_url", e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted">Model</label>
          <Input
            placeholder="gpt-4o / llama3.1"
            value={form.model}
            onChange={(e) => set("model", e.target.value)}
          />
        </div>
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-muted">
            API Key{" "}
            <span className="text-muted/60">(leave blank to keep existing)</span>
          </label>
          <div className="relative">
            <Input
              type={showKey ? "text" : "password"}
              placeholder="sk-…"
              value={form.api_key}
              onChange={(e) => set("api_key", e.target.value)}
              autoComplete="new-password"
            />
            <button
              type="button"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted hover:text-foreground"
              onClick={() => setShowKey((s) => !s)}
              tabIndex={-1}
            >
              <EyeOff className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-1 text-xs text-muted">
            API keys are encrypted at rest and never returned in responses.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Switch checked={form.enabled} onCheckedChange={(v) => set("enabled", v)} id="enabled" />
          <label htmlFor="enabled" className="text-sm">Enabled</label>
        </div>
        <div className="flex items-center gap-2">
          <Switch checked={form.is_default} onCheckedChange={(v) => set("is_default", v)} id="default" />
          <label htmlFor="default" className="text-sm">Set as default</label>
        </div>
      </div>
      {error && (
        <p className="flex items-center gap-1.5 text-xs text-destructive">
          <AlertCircle className="h-3.5 w-3.5" /> {error}
        </p>
      )}
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="secondary" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" size="sm" disabled={isPending}>
          {isPending && <Loader2 className="h-4 w-4 animate-spin" />} Save provider
        </Button>
      </div>
    </form>
  );
}

// ── Provider Card ─────────────────────────────────────────────────────────
function ProviderCard({ conn, onDelete }: { conn: ProviderConnection; onDelete: () => void }) {
  const testMutation = useTestProviderConnection();
  const updateMutation = useUpdateProviderConnection();
  const [showEdit, setShowEdit] = useState(false);

  const def = conn.provider_details;
  const isOk = !conn.last_error_code;
  const testRes = testMutation.data;

  const handleTest = () => testMutation.mutate(conn.id);
  const handleToggle = (enabled: boolean) =>
    updateMutation.mutate({ id: conn.id, data: { enabled } });

  return (
    <>
      <Card className={cn("transition-colors", conn.is_default && "border-primary/40 bg-primary/5", !conn.enabled && "opacity-60")}>
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted/20 text-muted">
                <Bot className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">
                  {conn.display_name || def.display_name}
                  {conn.is_default && (
                    <Badge variant="primary" className="ml-1.5 text-[10px]">default</Badge>
                  )}
                </p>
                <p className="truncate text-xs text-muted">{conn.model || "model not set"}</p>
                {conn.base_url && (
                  <p className="truncate text-xs text-muted/60">{conn.base_url}</p>
                )}
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-2">
              {conn.latency_ms != null && (
                <span className="text-xs text-muted">{conn.latency_ms}ms</span>
              )}
              {conn.status && normalizeStatus(conn.status) !== "connected" && (
                <Badge variant={statusTone(conn.status)} className="text-[10px]" title={conn.last_error_message || undefined}>
                  {statusLabel(conn.status)}
                </Badge>
              )}
              {isOk ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <Badge variant="critical" className="text-[10px]">
                  {normalizeErrorLabel(conn.last_error_code)}
                </Badge>
              )}
              <Switch checked={conn.enabled} onCheckedChange={handleToggle} />
            </div>
          </div>

          {/* Capabilities */}
          {def && (
            <div className="mt-3 flex flex-wrap gap-1">
              {def.supports_streaming && <Badge variant="default" className="text-[10px]">streaming</Badge>}
              {def.supports_tools && <Badge variant="default" className="text-[10px]">tools</Badge>}
              {def.supports_embeddings && <Badge variant="default" className="text-[10px]">embeddings</Badge>}
              {def.supports_model_discovery && <Badge variant="default" className="text-[10px]">model discovery</Badge>}
            </div>
          )}

          {/* Masked API key indicator */}
          {conn.api_key_masked && (
            <p className="mt-2 flex items-center gap-1 text-xs text-muted">
              <EyeOff className="h-3 w-3" /> {conn.api_key_masked}
            </p>
          )}

          {/* Test result */}
          {testRes && (
            <div className={cn("mt-2 rounded-md px-3 py-2 text-xs", testRes.status === "ok" ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400")}>
              {testRes.status === "ok"
                ? `Connected — ${testRes.latency_ms}ms`
                : `${normalizeErrorLabel(testRes.code ?? "")} — ${testRes.detail ?? ""}`}
            </div>
          )}

          {/* Actions */}
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" onClick={handleTest} disabled={testMutation.isPending}>
              {testMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Wifi className="h-3.5 w-3.5" />}
              Test
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowEdit(true)}>
              <Settings2 className="h-3.5 w-3.5" /> Edit
            </Button>
            <Button size="sm" variant="destructive" onClick={onDelete}>
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Edit dialog */}
      <Dialog open={showEdit} onOpenChange={setShowEdit}>
        <DialogContent>
          <DialogHeader title="Edit provider" description="Update configuration and credentials." />
          <ProviderForm
            initial={{ ...conn, provider_id: def.id }}
            onSave={async (data) => {
              await updateMutation.mutateAsync({ id: conn.id, data });
              setShowEdit(false);
            }}
            onCancel={() => setShowEdit(false)}
            isPending={updateMutation.isPending}
            error={updateMutation.error?.message}
          />
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Skills section ────────────────────────────────────────────────────────
function SkillsSection() {
  const { data: skillsList, isLoading } = useSkills();
  const { data: executions } = useSkillExecutions();
  const enable = useEnableSkill();
  const disable = useDisableSkill();
  const validate = useValidateSkill();
  const testSkill = useTestSkill();
  const [activeValidation, setActiveValidation] = useState<Record<string, { valid: boolean; errors: string[] }>>({});

  if (isLoading) return <div className="flex items-center gap-2 text-sm text-muted"><Loader2 className="h-4 w-4 animate-spin" /> Loading skills…</div>;
  if (!skillsList?.length) return <p className="text-sm text-muted">No skills installed. Add skill manifests to the skills/ directory.</p>;

  return (
    <div className="space-y-3">
      {(skillsList ?? []).map((skill) => (
        <Card key={skill.id} className={cn(!skill.enabled && "opacity-60")}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-primary" />
                  <span className="font-medium text-sm">{skill.name}</span>
                  <Badge variant="default" className="text-[10px]">{skill.category}</Badge>
                  <span className="text-xs text-muted">v{skill.version}</span>
                </div>
                <p className="mt-1 text-xs text-muted">{skill.description}</p>

                {skill.required_permissions.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {skill.required_permissions.map((p) => (
                      <Badge key={p} variant="warning" className="text-[10px]">{p}</Badge>
                    ))}
                  </div>
                )}

                {skill.required_integrations.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {skill.required_integrations.map((i) => (
                      <Badge key={i} variant="info" className="text-[10px]">needs: {i}</Badge>
                    ))}
                  </div>
                )}

                {/* Validation result */}
                {activeValidation[skill.id] && (
                  <div className={cn("mt-2 rounded-md px-3 py-2 text-xs", activeValidation[skill.id].valid ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400")}>
                    {activeValidation[skill.id].valid
                      ? "Valid ✓"
                      : activeValidation[skill.id].errors.join("; ")}
                  </div>
                )}
              </div>

              <Switch
                checked={skill.enabled}
                onCheckedChange={(on) =>
                  on ? enable.mutate(skill.id) : disable.mutate(skill.id)
                }
              />
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={async () => {
                  const res = await validate.mutateAsync(skill.id);
                  setActiveValidation((prev) => ({ ...prev, [skill.id]: res }));
                }}
                disabled={validate.isPending}
              >
                {validate.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                Validate
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => testSkill.mutate({ id: skill.id })}
                disabled={testSkill.isPending || !skill.enabled}
              >
                {testSkill.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Activity className="h-3.5 w-3.5" />}
                Test
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Execution history */}
      {executions && executions.results.length > 0 && (
        <div className="mt-4">
          <h3 className="mb-2 text-sm font-medium text-muted">Execution history</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border text-left text-muted">
                  <th className="pb-2 pr-4">Skill</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2 pr-4">Started</th>
                  <th className="pb-2">Duration</th>
                </tr>
              </thead>
              <tbody>
                {executions.results.slice(0, 10).map((log) => (
                  <tr key={log.id} className="border-b border-border/50">
                    <td className="py-2 pr-4 font-mono">{log.skill_id}</td>
                    <td className="py-2 pr-4">
                      <Badge
                        variant={log.status === "success" ? "success" : log.status === "running" ? "info" : "critical"}
                        className="text-[10px]"
                      >
                        {log.status}
                      </Badge>
                    </td>
                    <td className="py-2 pr-4 text-muted">
                      {new Date(log.started_at).toLocaleString()}
                    </td>
                    <td className="py-2 text-muted">
                      {log.latency_ms != null ? `${log.latency_ms}ms` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────
export default function DeveloperOptions() {
  const { data: conns, isLoading: connsLoading } = useProviderConnections();
  const createMutation = useCreateProviderConnection();
  const deleteMutation = useDeleteProviderConnection();
  const [showAdd, setShowAdd] = useState(false);
  const [activeTab, setActiveTab] = useState<"providers" | "skills" | "diagnostics">("providers");

  const connections = conns?.results ?? [];

  const tabs = [
    { id: "providers", label: "AI Providers" },
    { id: "skills", label: "Skills" },
    { id: "diagnostics", label: "Diagnostics" },
  ] as const;

  return (
    <div>
      <PageHeader
        title="Developer Options"
        description="Configure AI providers, manage skill registry, and diagnose connectivity."
      />

      {/* Tab bar */}
      <div className="mb-5 flex gap-1 rounded-lg border border-border bg-card-solid/40 p-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={cn(
              "flex-1 rounded-md px-3 py-1.5 text-sm transition-colors",
              activeTab === t.id
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted hover:text-foreground"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* PROVIDERS TAB */}
      {activeTab === "providers" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">
              Credentials are encrypted at rest. API keys are never returned in API responses.
            </p>
            <Button size="sm" onClick={() => setShowAdd(true)}>
              <Plus className="h-4 w-4" /> Add provider
            </Button>
          </div>

          {connsLoading && (
            <div className="flex items-center gap-2 text-sm text-muted">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading providers…
            </div>
          )}

          {!connsLoading && connections.length === 0 && (
            <Card>
              <CardContent className="py-8 text-center">
                <Bot className="mx-auto mb-2 h-8 w-8 text-muted/40" />
                <p className="text-sm text-muted">No providers configured.</p>
                <p className="mt-1 text-xs text-muted">
                  Add a provider to use cloud or local AI models.
                </p>
                <Button size="sm" className="mt-3" onClick={() => setShowAdd(true)}>
                  <Plus className="h-4 w-4" /> Add first provider
                </Button>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {connections.map((conn) => (
              <ProviderCard
                key={conn.id}
                conn={conn}
                onDelete={() => deleteMutation.mutate(conn.id)}
              />
            ))}
          </div>

          {/* Add provider dialog */}
          <Dialog open={showAdd} onOpenChange={setShowAdd}>
            <DialogContent>
              <DialogHeader title="Add AI provider" description="Credentials are encrypted and never stored as plaintext." />
              <ProviderForm
                onSave={async (data) => {
                  await createMutation.mutateAsync(data);
                  setShowAdd(false);
                }}
                onCancel={() => setShowAdd(false)}
                isPending={createMutation.isPending}
                error={createMutation.error?.message}
              />
            </DialogContent>
          </Dialog>
        </div>
      )}

      {/* SKILLS TAB */}
      {activeTab === "skills" && (
        <div>
          <p className="mb-4 text-sm text-muted">
            Skills are declarative capabilities loaded from JSON manifests. Enabling a skill allows the AI assistant to use it.
          </p>
          <SkillsSection />
        </div>
      )}

      {/* DIAGNOSTICS TAB */}
      {activeTab === "diagnostics" && <DiagnosticsSection />}
    </div>
  );
}

// ── Diagnostics (real probes from GET /api/health/) ──────────────────────
const SERVICE_ICONS: Record<string, React.ReactNode> = {
  database: <Server className="h-4 w-4" />,
  redis: <Zap className="h-4 w-4" />,
  celery: <Activity className="h-4 w-4" />,
  ai_provider: <Cpu className="h-4 w-4" />,
  github: <Bot className="h-4 w-4" />,
  google: <Wifi className="h-4 w-4" />,
};

function DiagnosticsSection() {
  const { data: health, isLoading, isError } = useSystemHealth();

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  if (isError || !health) {
    return <p className="text-sm text-red-500">Could not reach the health endpoint — check the backend is running.</p>;
  }

  const overallTone = health.status === "ok" ? "success" : health.status === "degraded" ? "warning" : "critical";
  const aiCheck = health.services["ai_provider"];
  const aiMode = typeof aiCheck?.mode === "string" ? aiCheck.mode : undefined;
  const integrations = Object.entries(health.integrations ?? {});

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm text-muted">Live probes from GET /api/health/</p>
        <Badge variant={overallTone}>{health.status}</Badge>
        {aiMode === "mock" && (
          <Badge variant="info" title="The deterministic offline mock provider is active — no external AI calls are made">
            Mock AI mode
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(health.services).map(([name, check]) => {
          const healthy = ["connected", "running", "configured"].includes(normalizeStatus(check.status));
          return (
            <Card key={name}>
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-2 text-sm capitalize">
                  {SERVICE_ICONS[name] ?? <Server className="h-4 w-4" />}
                  {name.replace(/_/g, " ")}
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={statusTone(check.status)} title={check.detail || undefined}>
                    {statusLabel(check.status)}
                  </Badge>
                  {healthy ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-muted" />
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {integrations.length > 0 && (
        <div className="rounded-lg border border-border p-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Your integrations</p>
          <div className="flex flex-wrap gap-2">
            {integrations.map(([platform, entry]) => (
              <Badge key={platform} variant={statusTone(entry.status)}>
                {platform}: {statusLabel(entry.status)}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-muted">
        Every status above is a real check (database, Redis, Celery workers, provider configuration) — nothing is
        hard-coded. For per-provider details, use &quot;Test Connection&quot;.
      </p>
    </div>
  );
}
