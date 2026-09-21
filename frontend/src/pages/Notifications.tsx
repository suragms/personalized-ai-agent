import { Bell, CheckCheck, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { useMarkAllRead, useNotifications, useSweep } from "@/hooks";
import { useWebSocket } from "@/hooks/useWebSocket";
import { cn, relativeTime } from "@/lib/utils";

const severityVariant = (s: string) => (s === "critical" ? "critical" : s === "warning" ? "warning" : "info");

export default function Notifications() {
  const queryClient = useQueryClient();
  const { data } = useNotifications();
  const markAllRead = useMarkAllRead();
  const sweep = useSweep();

  useWebSocket("/ws/notifications/", (msg) => {
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
    queryClient.invalidateQueries({ queryKey: ["unread"] });
    toast.info(msg.title || "New notification alert");
  });

  const notifications = data?.results ?? [];
  const unreadCount = notifications.filter((n) => !n.read).length;


  return (
    <div>
      <PageHeader
        title="Notifications"
        description="Actionable alerts from your agents — deadlines, inactive repos, project delays."
        action={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => void sweep.mutateAsync().then((r) => toast.info(`${r.created} new notification(s)`))} disabled={sweep.isPending}>
              <RefreshCw className={cn("h-4 w-4", sweep.isPending && "animate-spin")} /> Run sweep
            </Button>
            <Button variant="secondary" size="sm" onClick={() => { void markAllRead.mutateAsync(); toast.success("All marked read"); }}>
              <CheckCheck className="h-4 w-4" /> Mark all read
            </Button>
          </div>
        }
      />

      {unreadCount > 0 && (
        <p className="mb-3 text-sm text-muted">
          <Bell className="mr-1 inline h-4 w-4" />
          {unreadCount} unread
        </p>
      )}

      {notifications.length === 0 ? (
        <EmptyState title="Inbox zero" description="Run the notification sweep or agents to populate alerts." />
      ) : (
        <Card>
          <CardContent className="divide-y divide-border/60 p-0">
            {notifications.map((n) => (
              <div key={n.id} className={cn("flex items-start gap-3 p-3.5", !n.read && "bg-primary/[0.03]")}>
                <span
                  className={cn(
                    "mt-1.5 h-2 w-2 shrink-0 rounded-full",
                    n.severity === "critical" ? "bg-[#d03b3b]" : n.severity === "warning" ? "bg-[#fab219]" : "bg-[#22d3ee]"
                  )}
                />
                <div className="min-w-0 flex-1">
                  <p className={cn("text-sm", !n.read && "font-medium")}>{n.title}</p>
                  {n.body && <p className="text-xs text-muted">{n.body}</p>}
                  <p className="mt-0.5 text-[11px] text-muted/70">{n.kind} · {relativeTime(n.created_at)}</p>
                </div>
                <Badge variant={severityVariant(n.severity)}>{n.severity}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
