import { useState, type FormEvent } from "react";
import { BrainCircuit, LogIn, Sparkles } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden p-4">
      <div className="bg-grid absolute inset-0 opacity-60" aria-hidden />
      <div className="absolute -top-32 left-1/2 h-80 w-[36rem] -translate-x-1/2 rounded-full bg-[#6366f1]/20 blur-3xl" aria-hidden />
      <div className="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-[#22d3ee]/15 blur-3xl" aria-hidden />

      <div className="glass relative w-full max-w-sm rounded-xl p-8">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[#6366f1] to-[#22d3ee]">
            <BrainCircuit className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">Personalized AI Agent</h1>
            <p className="flex items-center justify-center gap-1 text-xs text-muted">
              <Sparkles className="h-3 w-3" /> Your personal intelligence operating system
            </p>
          </div>
        </div>

        <form onSubmit={onSubmit} className="space-y-3">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted">Username</label>
            <Input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted">Password</label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
          </div>
          {error && <p className="text-xs text-[#d03b3b]">{error}</p>}
          <Button type="submit" variant="gradient" size="lg" className="w-full" disabled={busy}>
            <LogIn className="h-4 w-4" /> {busy ? "Signing in…" : "Sign in"}
          </Button>
        </form>

        <p className="mt-4 rounded-lg border border-border/50 bg-surface/50 p-3 text-xs text-muted">
          No account yet? Contact your administrator, or create one locally with{" "}
          <code className="rounded bg-background/80 px-1 py-0.5 text-foreground">python manage.py createsuperuser</code>.
          Seeded development credentials are documented in the README for local development only.
        </p>
      </div>
    </div>
  );
}
