import { useState } from "react";
import { CalendarDays, CheckCircle2, ListTodo, Moon, Sunrise } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MarkdownView } from "@/components/MarkdownView";
import { EmptyState } from "@/components/ui/empty-state";
import { useBriefing, useCalendar, useGenerateBriefing, useTasks, useUpdateTask } from "@/hooks";
import type { Task } from "@/types";
import { cn, shortDate } from "@/lib/utils";

const priorityVariant = (p: Task["priority"]) =>
  p === "urgent" ? "critical" : p === "high" ? "warning" : p === "medium" ? "info" : "default";
const statusVariant = (s: Task["status"]) =>
  s === "done" ? "success" : s === "in_progress" ? "primary" : s === "blocked" ? "critical" : "default";

export default function TasksCalendar() {
  const [tab, setTab] = useState("briefing");
  const { data: tasks } = useTasks();
  const { data: calendar } = useCalendar();
  const { data: morning } = useBriefing("morning");
  const { data: eod } = useBriefing("eod");
  const generate = useGenerateBriefing();
  const updateTask = useUpdateTask();

  const all = tasks?.results ?? [];
  const done = all.filter((t) => t.status === "done");
  const open = all.filter((t) => t.status !== "done");

  function changeStatus(task: Task, status: Task["status"]) {
    updateTask.mutate({ id: task.id, patch: { status } }, { onSuccess: () => toast.success(`Task "${task.title}" → ${status}`) });
  }

  async function onBriefing(kind: "morning" | "eod") {
    await generate.mutateAsync(kind);
    toast.success(kind === "morning" ? "Morning briefing generated" : "End-of-day wrap-up generated");
  }

  return (
    <div>
      <PageHeader title="Tasks & Calendar" description="Priorities, deadlines, and your day plan." />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="briefing">
                <Sunrise className="mr-1 h-3.5 w-3.5" /> Briefings
              </TabsTrigger>
              <TabsTrigger value="tasks">
                <ListTodo className="mr-1 h-3.5 w-3.5" /> Tasks ({open.length})
              </TabsTrigger>
              <TabsTrigger value="calendar">
                <CalendarDays className="mr-1 h-3.5 w-3.5" /> Calendar
              </TabsTrigger>
            </TabsList>

            <TabsContent value="briefing">
              <div className="mb-3 flex gap-2">
                <Button size="sm" onClick={() => onBriefing("morning")}>
                  <Sunrise className="h-4 w-4" /> Generate morning briefing
                </Button>
                <Button size="sm" variant="secondary" onClick={() => onBriefing("eod")}>
                  <Moon className="h-4 w-4" /> Generate EOD wrap-up
                </Button>
              </div>
              <Card>
                <CardContent className="max-h-[30rem] space-y-4 overflow-y-auto p-4">
                  {morning?.results?.[0] && (
                    <div>
                      <p className="mb-1 text-xs font-medium text-muted">MORNING · {shortDate(morning.results[0].date)}</p>
                      <MarkdownView content={morning.results[0].content} />
                    </div>
                  )}
                  {eod?.results?.[0] && (
                    <div className="border-t border-border pt-4">
                      <p className="mb-1 text-xs font-medium text-muted">END OF DAY · {shortDate(eod.results[0].date)}</p>
                      <MarkdownView content={eod.results[0].content} />
                    </div>
                  )}
                  {!morning?.results?.[0] && !eod?.results?.[0] && (
                    <EmptyState title="No briefings yet" description="Generate a morning briefing to see today's priorities, workload, and risk analysis." />
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="tasks">
              <Card>
                <CardContent className="space-y-1.5 p-3">
                  {open.length === 0 && <EmptyState title="All caught up" description="No open tasks — enjoy the moment!" />}
                  {open.map((task) => (
                    <div key={task.id} className="group flex items-center gap-3 rounded-md border border-border/70 p-2.5 hover:bg-muted/5">
                      <button
                        className="rounded-full border-2 border-muted/40 p-0.5 transition-colors hover:border-primary"
                        onClick={() => changeStatus(task, "done")}
                        aria-label={`Mark ${task.title} done`}
                      >
                        <CheckCircle2 className="h-4 w-4 text-transparent group-hover:text-primary/50" />
                      </button>
                      <div className="min-w-0 flex-1">
                        <p className={cn("truncate text-sm", task.status === "done" && "line-through opacity-60")}>{task.title}</p>
                        <p className="text-xs text-muted">
                          {task.priority} · {task.due_date ? `due ${shortDate(task.due_date)}` : "no due date"}
                          {task.project_name ? ` · ${task.project_name}` : ""}
                        </p>
                      </div>
                      <Badge variant={priorityVariant(task.priority)}>{task.priority}</Badge>
                      <Badge variant={statusVariant(task.status)}>{task.status}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="calendar">
              <Card>
                <CardContent className="p-4">
                  {(calendar?.results ?? []).length === 0 && <EmptyState title="No events today" description="Your calendar is clear." />}
                  <div className="space-y-2">
                    {(calendar?.results ?? []).map((event) => (
                      <div key={event.id} className="flex items-center gap-3 rounded-md border border-border/70 p-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                          <CalendarDays className="h-4 w-4 text-primary" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium">{event.title}</p>
                          <p className="text-xs text-muted">
                            {new Date(event.start).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })} –{" "}
                            {new Date(event.end).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}
                          </p>
                        </div>
                        {event.location && <span className="text-xs text-muted">{event.location}</span>}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Summary column */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Task summary</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-2 text-center">
              <div className="rounded-lg bg-muted/10 p-3">
                <p className="text-2xl font-semibold tabular-nums">{done.length}</p>
                <p className="text-xs text-muted">Done</p>
              </div>
              <div className="rounded-lg bg-muted/10 p-3">
                <p className="text-2xl font-semibold tabular-nums">{open.length}</p>
                <p className="text-xs text-muted">Open</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
