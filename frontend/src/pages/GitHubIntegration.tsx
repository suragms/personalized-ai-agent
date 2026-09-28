import { useEffect, useState } from "react";
import { CheckCircle, Github, Loader2, AlertCircle } from "lucide-react";
import { useGitHubStatus, useGitHubSync, useGitHubDisconnect } from "@/hooks/useIntelligence";
import { githubOAuth } from "@/services/intelligence";
import { Button } from "@/components/ui/button";

export default function GitHubIntegration() {
  const { data: status, isLoading, refetch } = useGitHubStatus();
  const syncMutation = useGitHubSync();
  const disconnectMutation = useGitHubDisconnect();
  const [isConnecting, setIsConnecting] = useState(false);

  // Handle OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");

    if (code && state) {
      handleOAuthCallback(code, state);
    }
  }, []);

  const handleOAuthCallback = async (code: string, state: string) => {
    setIsConnecting(true);
    try {
      const redirectUri = `${window.location.origin}/integrations/github`;
      await githubOAuth.callback(code, state, redirectUri);

      // Clear URL parameters
      window.history.replaceState({}, "", "/integrations/github");

      // Refetch status
      await refetch();
    } catch (_error) {
      // OAuth callback error — do not log sensitive data
    } finally {
      setIsConnecting(false);
    }
  };

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      const redirectUri = `${window.location.origin}/integrations/github`;
      const { authorization_url } = await githubOAuth.initiate(redirectUri);

      // Redirect to GitHub
      window.location.href = authorization_url;
    } catch (_error) {
      // OAuth initiation error — do not log sensitive data
      setIsConnecting(false);
    }
  };

  const handleSync = () => {
    syncMutation.mutate();
  };

  const handleDisconnect = () => {
    if (confirm("Are you sure you want to disconnect GitHub? Your data will remain but won't be updated.")) {
      disconnectMutation.mutate();
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted" />
      </div>
    );
  }

  const connected = status?.connected ?? false;
  const syncing = syncMutation.isPending;

  return (
    <div className="container mx-auto max-w-4xl space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[#6366f1] to-[#22d3ee]">
            <Github className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold">GitHub Integration</h1>
            <p className="text-sm text-muted">
              {connected ? "Connected and syncing your development activity" : "Connect to analyze your repositories"}
            </p>
          </div>
        </div>
      </div>

      {/* Connection Status Card */}
      <div className="glass rounded-xl p-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h2 className="font-semibold">Connection Status</h2>
                {connected && <CheckCircle className="h-5 w-5 text-green-500" />}
                {!connected && !isConnecting && <AlertCircle className="h-5 w-5 text-muted" />}
                {isConnecting && <Loader2 className="h-5 w-5 animate-spin text-muted" />}
              </div>
              <p className="text-sm text-muted">
                {isConnecting && "Connecting..."}
                {!isConnecting && connected && `Connected as ${status?.account}`}
                {!isConnecting && !connected && "Not connected"}
              </p>
            </div>

            {connected ? (
              <div className="flex gap-2">
                <Button
                  onClick={handleSync}
                  disabled={syncing}
                  variant="gradient"
                  size="sm"
                >
                  {syncing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Syncing...
                    </>
                  ) : (
                    "Sync Now"
                  )}
                </Button>
                <Button
                  onClick={handleDisconnect}
                  disabled={disconnectMutation.isPending}
                  variant="ghost"
                  size="sm"
                >
                  Disconnect
                </Button>
              </div>
            ) : (
              <Button
                onClick={handleConnect}
                disabled={isConnecting}
                variant="gradient"
              >
                {isConnecting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Github className="h-4 w-4" />
                    Connect GitHub
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Last Sync Info */}
          {connected && status && (
            <div className="border-t border-border/40 pt-4">
              <div className="grid gap-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted">Last synchronized:</span>
                  <span className="font-medium">
                    {status.last_synced_at
                      ? new Date(status.last_synced_at).toLocaleString()
                      : "Not yet synchronized"}
                  </span>
                </div>

                {status.last_error && (
                  <div className="flex items-start gap-2 rounded-lg bg-red-500/10 p-3">
                    <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-500" />
                    <div className="space-y-1">
                      <p className="font-medium text-red-500">Sync Error</p>
                      <p className="text-xs text-red-400">{status.last_error}</p>
                    </div>
                  </div>
                )}

                {syncMutation.isError && (
                  <div className="flex items-start gap-2 rounded-lg bg-red-500/10 p-3">
                    <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-500" />
                    <div className="space-y-1">
                      <p className="font-medium text-red-500">Sync Failed</p>
                      <p className="text-xs text-red-400">
                        {syncMutation.error instanceof Error ? syncMutation.error.message : "Unknown error"}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sync Result */}
      {syncMutation.isSuccess && syncMutation.data && (
        <div className="glass rounded-xl p-6">
          <h3 className="mb-4 font-semibold">Latest Sync</h3>
          <div className="grid gap-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted">Repositories:</span>
              <span className="font-medium">{syncMutation.data.repositories}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Commits:</span>
              <span className="font-medium">{syncMutation.data.commits}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Pull Requests:</span>
              <span className="font-medium">{syncMutation.data.pull_requests}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Issues:</span>
              <span className="font-medium">{syncMutation.data.issues}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Releases:</span>
              <span className="font-medium">{syncMutation.data.releases}</span>
            </div>

            {syncMutation.data.errors.length > 0 && (
              <div className="mt-2 space-y-1 rounded-lg bg-orange-500/10 p-3">
                <p className="font-medium text-orange-500">Warnings:</p>
                {syncMutation.data.errors.map((error, i) => (
                  <p key={i} className="text-xs text-orange-400">
                    {error}
                  </p>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!connected && !isConnecting && (
        <div className="glass rounded-xl p-8 text-center">
          <Github className="mx-auto mb-4 h-12 w-12 text-muted" />
          <h3 className="mb-2 text-lg font-semibold">Connect Your GitHub Account</h3>
          <p className="mb-6 text-sm text-muted">
            Analyze your repositories, commits, pull requests, and development patterns.
            All data is stored securely and never shared.
          </p>
          <Button onClick={handleConnect} variant="gradient">
            <Github className="h-4 w-4" />
            Connect GitHub
          </Button>
        </div>
      )}
    </div>
  );
}
