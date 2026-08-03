import { Bot, Cpu, KeyRound, Moon, Sun, UserRound } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { useProviders } from "@/hooks";
import { cn } from "@/lib/utils";

export default function Settings() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const { data: providers } = useProviders();

  return (
    <div>
      <PageHeader title="Settings" description="Profile, appearance, and AI provider configuration." />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <UserRound className="h-4 w-4" /> Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted">Username</span>
              <span className="font-medium">{user?.username}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted">Email</span>
              <span className="font-medium">{user?.email}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted">Role</span>
              <Badge variant="primary">{user?.role}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted">GitHub</span>
              <span className="font-medium">{user?.github_username || "—"}</span>
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
              <Switch checked={theme === "dark"} onCheckedChange={(on) => setTheme(on ? "dark" : "light")} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm">Provider</p>
                <p className="text-xs text-muted">Configure in <code className="font-mono text-[11px]">.env</code> → AI_PROVIDER</p>
              </div>
              <Badge variant="info">settings.env</Badge>
            </div>
          </CardContent>
        </Card>

        {/* AI providers */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <Cpu className="h-4 w-4" /> AI providers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {(providers?.providers ?? []).map((p) => (
                <div key={p.name} className={cn("flex items-center justify-between rounded-lg border p-3", p.active && "border-primary/50 bg-primary/5")}>
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
            </div>
            <p className="mt-3 flex items-center gap-1.5 text-xs text-muted">
              <KeyRound className="h-3.5 w-3.5" />
              Keys live in the backend environment, never the browser. Set <code className="font-mono text-[11px]">AI_PROVIDER</code> and restart.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
